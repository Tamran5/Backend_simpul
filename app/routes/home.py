# app/routes/home.py

from datetime import datetime, date

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import User, WeddingPlan, Task, LegalDocument, Notification, JourneyStepProgress
from app.services import pair_service, journey_service
from app.services.mail_service import send_wedding_date_update_email
from app.utils.helpers import format_date_display, date_to_epoch

home_bp = Blueprint('home', __name__, url_prefix='/api')


# ── GET /api/home ─────────────────────────────────────────────────────────────

@home_bp.route('/home', methods=['GET'])
@jwt_required()
def get_home():
    user      = User.query.get_or_404(get_jwt_identity())
    pair_info = pair_service.get_pair_info(user)

    return jsonify({
        'data': {
            'user':                  _user_dict(user),
            'pair':                  pair_info,
            'wedding_date_display':  _get_wedding_display(user, pair_info),
            'wedding_date_epoch':    _get_wedding_epoch(user, pair_info),
            'progress':              _get_progress(user, pair_info),
            'legal':                 _get_legal_status(user, pair_info),
        }
    }), 200


# ── PATCH /api/wedding-date ───────────────────────────────────────────────────

@home_bp.route('/wedding-date', methods=['PATCH'])
@jwt_required()
def update_wedding_date():
    user     = User.query.get_or_404(get_jwt_identity())
    data     = request.get_json() or {}
    date_str = data.get('date', '').strip()

    if not date_str:
        return jsonify({'status': 'fail', 'message': 'Field "date" wajib diisi (YYYY-MM-DD).'}), 400

    try:
        parsed = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'status': 'fail', 'message': 'Format tanggal tidak valid. Gunakan YYYY-MM-DD.'}), 422

    if parsed < date.today():
        return jsonify({'status': 'fail', 'message': 'Tanggal tidak boleh di masa lalu.'}), 422

    # Upsert
    plan = WeddingPlan.query.filter_by(user_id=user.id).first()
    if plan:
        plan.wedding_date = parsed
    else:
        plan = WeddingPlan(user_id=user.id, wedding_date=parsed)
        db.session.add(plan)
    db.session.commit()

    # Notif ke pasangan
    pair_info = pair_service.get_pair_info(user)
    if pair_info['is_synced'] and pair_info.get('partner'):
        partner = User.query.get(pair_info['partner']['id'])
        if partner:
            display = format_date_display(parsed)
            send_wedding_date_update_email(partner.name, partner.email, user.name, display)
            db.session.add(Notification(
                user_id    = partner.id,
                title      = 'Tanggal pernikahan diperbarui 📅',
                body       = f'{user.name} mengubah tanggal pernikahan menjadi {display}.',
                notif_type = 'info',
            ))
            db.session.commit()

    return jsonify({
        'status':  'success',
        'message': 'Tanggal pernikahan berhasil disimpan.',
        'data': {
            'display': format_date_display(parsed),
            'epoch':   date_to_epoch(parsed),
        },
    }), 200


# ── Private helpers ───────────────────────────────────────────────────────────

def _user_dict(user: User) -> dict:
    return {
        'id':          user.id,
        'name':        user.name,
        'photo_url':   user.photo_url or '',
        'unique_code': user.unique_code,
    }


def _get_wedding_display(user: User, pair_info: dict) -> str:
    plan = WeddingPlan.query.filter_by(user_id=user.id).first()
    if plan and plan.wedding_date:
        return format_date_display(plan.wedding_date)
    # Fallback ke tanggal pasangan
    if pair_info['is_synced'] and pair_info.get('partner'):
        p_plan = WeddingPlan.query.filter_by(user_id=pair_info['partner']['id']).first()
        if p_plan and p_plan.wedding_date:
            return format_date_display(p_plan.wedding_date)
    return ''


def _get_wedding_epoch(user: User, pair_info: dict) -> int:
    plan = WeddingPlan.query.filter_by(user_id=user.id).first()
    if plan and plan.wedding_date:
        return date_to_epoch(plan.wedding_date)
    if pair_info['is_synced'] and pair_info.get('partner'):
        p_plan = WeddingPlan.query.filter_by(user_id=pair_info['partner']['id']).first()
        if p_plan and p_plan.wedding_date:
            return date_to_epoch(p_plan.wedding_date)
    return 0


def _get_progress(user: User, pair_info: dict) -> dict:
    ids = [user.id]
    if pair_info['is_synced'] and pair_info.get('partner'):
        ids.append(pair_info['partner']['id'])

    # Tugas umum (non-legal) — tetap dari tabel Task jika ada
    task_total = Task.query.filter(Task.user_id.in_(ids)).count()
    task_done  = Task.query.filter(Task.user_id.in_(ids), Task.is_done == True).count()

    # Checklist legal sekarang berbasis JourneyStepProgress (sama seperti
    # halaman To Do), bukan tabel Task lagi — hitung dari sana agar
    # angka di Home konsisten dengan halaman Todo.
    legal_total = 0
    legal_done = 0
    for uid in ids:
        u = User.query.get(uid)
        if not u:
            continue
        steps = journey_service.get_steps_for_user(u)
        progress_rows = JourneyStepProgress.query.filter_by(user_id=uid).all()
        merged = journey_service.merge_with_progress(steps, progress_rows)
        legal_total += len(merged)
        legal_done += sum(1 for s in merged if s['is_done'])

    total = task_total + legal_total
    done  = task_done + legal_done

    return {
        'total':         total,
        'completed':     done,
        'legal_percent': round(legal_done / legal_total * 100) if legal_total else 0,
        'task_percent':  round(task_done / task_total * 100) if task_total else 0,
    }


def _get_legal_status(user: User, pair_info: dict) -> dict:
    ids = [user.id]
    if pair_info['is_synced'] and pair_info.get('partner'):
        ids.append(pair_info['partner']['id'])

    kelurahan_done = JourneyStepProgress.query.filter(
        JourneyStepProgress.user_id.in_(ids),
        JourneyStepProgress.step_key == 'kelurahan_n1n4',
        JourneyStepProgress.is_done == True,
    ).first() is not None

    return {
        'current_doc': '' if kelurahan_done else 'N1-N4',
        'level':       '' if kelurahan_done else 'Kelurahan',
        'percent':     100 if kelurahan_done else 0,
    }