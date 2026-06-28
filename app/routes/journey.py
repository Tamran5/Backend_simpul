import os
import uuid
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import User, Notification, JourneyStepProgress
from app.services import journey_service, pair_service

journey_bp = Blueprint('journey', __name__, url_prefix='/api/journey')

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE_MB = 10


# ── GET /api/journey ──────────────────────────────────────────────────────────

@journey_bp.route('', methods=['GET'])
@jwt_required()
def get_journey():
    user = User.query.get_or_404(get_jwt_identity())

    steps = journey_service.get_steps_for_user(user)
    progress_rows = JourneyStepProgress.query.filter_by(user_id=user.id).all()
    merged = journey_service.merge_with_progress(steps, progress_rows)

    # Cek & kirim notifikasi pengingat bimbingan pranikah jika ada step
    # bimbingan yang baru saja terbuka (unlocked) dan belum pernah dinotif.
    _notify_newly_unlocked_guidance(user, merged, progress_rows)

    done_count = sum(1 for s in merged if s['is_done'])

    return jsonify({
        'status': 'success',
        'data': {
            'profile': {
                'religion':       user.religion,
                'gender':         user.gender,
                'is_out_of_town': user.is_out_of_town,
                'is_foreigner':   user.is_foreigner,
            },
            'steps':       merged,
            'total_steps': len(merged),
            'done_steps':  done_count,
        },
    }), 200


# ── POST /api/journey/<step_key>/toggle ───────────────────────────────────────

@journey_bp.route('/<string:step_key>/toggle', methods=['POST'])
@jwt_required()
def toggle_step(step_key):
    user = User.query.get_or_404(get_jwt_identity())

    steps = journey_service.get_steps_for_user(user)
    step_keys_in_order = [s['step_key'] for s in steps]
    if step_key not in step_keys_in_order:
        return jsonify({'status': 'fail', 'message': 'Langkah tidak ditemukan untuk profil Anda.'}), 404

    progress_rows = JourneyStepProgress.query.filter_by(user_id=user.id).all()
    progress_map = {p.step_key: p for p in progress_rows}

    # Validasi lock: tidak boleh toggle jika step sebelumnya belum selesai.
    idx = step_keys_in_order.index(step_key)
    if idx > 0:
        prev_key = step_keys_in_order[idx - 1]
        prev_done = progress_map.get(prev_key) and progress_map[prev_key].is_done
        current_done = progress_map.get(step_key) and progress_map[step_key].is_done
        if not prev_done and not current_done:
            return jsonify({
                'status': 'fail',
                'message': 'Sistem mendeteksi urutan berkas di atasnya belum terpenuhi.',
            }), 422

    row = progress_map.get(step_key)

    
    step_obj = next(s for s in steps if s['step_key'] == step_key)
    is_currently_done = row.is_done if row else False
    will_be_done = not is_currently_done

    if step_obj.get('requires_document') and will_be_done and not (row and row.document_path):
        return jsonify({
            'status': 'fail',
            'message': 'Unggah dokumen terlebih dahulu sebelum menandai langkah ini selesai.',
        }), 422

    if not row:
        row = JourneyStepProgress(user_id=user.id, step_key=step_key, is_done=False)
        db.session.add(row)

    row.is_done = will_be_done
    row.updated_at = datetime.utcnow()
    db.session.commit()

    # Re-fetch progress terbaru lalu cek apakah ada step bimbingan yang baru terbuka.
    progress_rows = JourneyStepProgress.query.filter_by(user_id=user.id).all()
    merged = journey_service.merge_with_progress(steps, progress_rows)
    _notify_newly_unlocked_guidance(user, merged, progress_rows)

    return jsonify({
        'status': 'success',
        'message': 'Status langkah berhasil diperbarui.',
        'data': {'step_key': step_key, 'is_done': row.is_done},
    }), 200


# ── POST /api/journey/<step_key>/upload ───────────────────────────────────────

@journey_bp.route('/<string:step_key>/upload', methods=['POST'])
@jwt_required()
def upload_document(step_key):
    user = User.query.get_or_404(get_jwt_identity())

    steps = journey_service.get_steps_for_user(user)
    step_keys_in_order = [s['step_key'] for s in steps]
    if step_key not in step_keys_in_order:
        return jsonify({'status': 'fail', 'message': 'Langkah tidak ditemukan untuk profil Anda.'}), 404

    progress_rows = JourneyStepProgress.query.filter_by(user_id=user.id).all()
    progress_map = {p.step_key: p for p in progress_rows}

    # Validasi lock (sama seperti toggle).
    idx = step_keys_in_order.index(step_key)
    if idx > 0:
        prev_key = step_keys_in_order[idx - 1]
        prev_done = progress_map.get(prev_key) and progress_map[prev_key].is_done
        if not prev_done:
            return jsonify({
                'status': 'fail',
                'message': 'Anda wajib menyelesaikan dan mengunggah berkas pada langkah sebelumnya terlebih dahulu agar tertib administrasi.',
            }), 422

    if 'file' not in request.files:
        return jsonify({'status': 'fail', 'message': 'Tidak ada berkas yang dikirim.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'fail', 'message': 'Nama berkas tidak valid.'}), 400

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({
            'status': 'fail',
            'message': 'Format berkas tidak didukung. Gunakan PDF, JPG, atau PNG.',
        }), 422

    # Simulasi penyimpanan lokal (ganti ke S3/cloud storage di production).
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads', 'journey_docs', str(user.id))
    os.makedirs(upload_dir, exist_ok=True)

    safe_name = secure_filename(file.filename)
    stored_name = f'{uuid.uuid4().hex}_{safe_name}'
    full_path = os.path.join(upload_dir, stored_name)
    file.save(full_path)

    relative_path = f'/uploads/journey_docs/{user.id}/{stored_name}'

    row = progress_map.get(step_key)
    if not row:
        row = JourneyStepProgress(user_id=user.id, step_key=step_key)
        db.session.add(row)

    row.document_path = relative_path
    row.document_name = safe_name
    row.is_done = True  # konsisten dengan logic lama: upload otomatis menandai selesai
    row.updated_at = datetime.utcnow()
    db.session.commit()

    progress_rows = JourneyStepProgress.query.filter_by(user_id=user.id).all()
    merged = journey_service.merge_with_progress(steps, progress_rows)
    _notify_newly_unlocked_guidance(user, merged, progress_rows)

    return jsonify({
        'status': 'success',
        'message': 'Berkas berhasil diunggah.',
        'data': {
            'step_key':      step_key,
            'document_path': relative_path,
            'document_name': safe_name,
            'is_done':       True,
        },
    }), 200


# ── GET /api/journey/<step_key>/info ──────────────────────────────────────────

@journey_bp.route('/<string:step_key>/info', methods=['GET'])
@jwt_required()
def get_step_info(step_key):
    user = User.query.get_or_404(get_jwt_identity())
    steps = journey_service.get_steps_for_user(user)

    step = next((s for s in steps if s['step_key'] == step_key), None)
    if not step:
        return jsonify({'status': 'fail', 'message': 'Langkah tidak ditemukan.'}), 404

    return jsonify({'status': 'success', 'data': step}), 200


# ── GET /api/journey/partner ──────────────────────────────────────────────────
#
# Versi READ-ONLY dari journey milik pasangan. Tidak ada endpoint
# toggle/upload yang menerima target_user_id — setiap aksi tulis selalu
# memakai get_jwt_identity() milik pemanggil sendiri (lihat toggle_step &
# upload_document di atas), jadi user A secara desain tidak bisa mengubah
# data user B lewat permukaan API manapun. Endpoint ini sengaja TIDAK
# menyediakan rute toggle/upload versi "partner".

@journey_bp.route('/partner', methods=['GET'])
@jwt_required()
def get_partner_journey():
    user = User.query.get_or_404(get_jwt_identity())
    pair_info = pair_service.get_pair_info(user)

    if not pair_info.get('is_synced') or not pair_info.get('partner'):
        return jsonify({
            'status': 'fail',
            'message': 'Anda belum terhubung dengan pasangan.',
        }), 400

    partner_id = pair_info['partner']['id']
    partner = User.query.get_or_404(partner_id)

    steps = journey_service.get_steps_for_user(partner)
    progress_rows = JourneyStepProgress.query.filter_by(user_id=partner.id).all()
    merged = journey_service.merge_with_progress(steps, progress_rows)

    # Catatan privasi: requirements & step_by_step tetap disertakan supaya
    # pasangan bisa membantu mengingatkan/menyiapkan dokumen, tapi nama file
    # dokumen yang sudah diunggah TIDAK ditampilkan secara verbatim — hanya
    # status apakah sudah/belum, untuk menjaga privasi berkas (KTP, akta, dst).
    sanitized = [
        {
            **{k: v for k, v in step.items() if k != 'document_name'},
        }
        for step in merged
    ]

    done_count = sum(1 for s in sanitized if s['is_done'])

    return jsonify({
        'status': 'success',
        'data': {
            'partner_name': partner.name,
            'profile': {
                'religion':       partner.religion,
                'gender':         partner.gender,
                'is_out_of_town': partner.is_out_of_town,
                'is_foreigner':   partner.is_foreigner,
            },
            'steps':       sanitized,
            'total_steps': len(sanitized),
            'done_steps':  done_count,
        },
    }), 200


# ── Private helpers ───────────────────────────────────────────────────────────

def _notify_newly_unlocked_guidance(user, merged_steps, progress_rows):
    """
    Kirim notifikasi pengingat saat step kategori "bimbingan pranikah"
    (lintas agama: Suscatin/KPP/Katekisasi) berubah status dari terkunci
    menjadi terbuka — yaitu begitu langkah persis sebelumnya ditandai selesai.
    Notifikasi hanya dikirim sekali per step per user (guidance_notified flag).
    """
    progress_map = {p.step_key: p for p in progress_rows}

    for step in merged_steps:
        key = step['step_key']
        if not journey_service.is_guidance_step(key):
            continue
        if step['is_locked']:
            continue  # belum terbuka, belum perlu notif

        row = progress_map.get(key)
        already_notified = row.guidance_notified if row else False
        if already_notified:
            continue

        if not row:
            row = JourneyStepProgress(user_id=user.id, step_key=key, is_done=False)
            db.session.add(row)

        row.guidance_notified = True

        db.session.add(Notification(
            user_id    = user.id,
            title      = 'Saatnya Bimbingan Pranikah 💍',
            body       = f'Langkah "{step["title"]}" sudah terbuka. Jangan lupa jadwalkan sesi bimbingan di {step["target_institution"]} ya.',
            notif_type = 'task',
        ))

    db.session.commit()