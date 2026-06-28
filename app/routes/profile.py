# app/routes/profile.py

import os
import random
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models import User
from app.services.mail_service import send_otp_email
from app.utils.helpers import allowed_file

profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')


# ── GET /api/profile ──────────────────────────────────────────────────────────

@profile_bp.route('', methods=['GET'])
@jwt_required()
def get_profile():
    user = _get_user_or_404()
    return jsonify({
        'status': 'success',
        'data': {
            'id':           user.id,
            'name':         user.name,
            'email':        user.email,
            'phone':        user.phone or '',
            'gender':       user.gender,
            'religion':     user.religion,
            'photo_url':    user.photo_url or '',
            'unique_code':  user.unique_code,
            'is_synced':    user.sync_status == 'synced',
            'sync_status':  user.sync_status,
            'partner_name': user.partner_name or '',
        },
    }), 200


# ── POST /api/profile/update ──────────────────────────────────────────────────
# Mendukung perubahan nama/telepon biasa, dan perubahan email (butuh OTP).

@profile_bp.route('/update', methods=['POST'])
@jwt_required()
def update_profile():
    user      = _get_user_or_404()
    data      = request.get_json() or {}
    new_name  = data.get('name', user.name).strip()
    new_email = data.get('email', user.email).strip().lower()
    new_phone = data.get('phone', user.phone or '').strip()
    otp_input = data.get('otp', '').strip()

    # ── Ubah email: butuh verifikasi OTP ke email lama ────────────────────────
    if new_email != user.email.lower():
        if not otp_input:
            return _send_email_change_otp(user)

        if user.otp_code != otp_input or datetime.utcnow() > user.otp_expiry:
            return jsonify({'status': 'fail', 'message': 'OTP salah atau sudah kedaluwarsa.'}), 400

        if User.query.filter(User.email == new_email, User.id != user.id).first():
            return jsonify({'status': 'fail', 'message': 'Email sudah digunakan akun lain.'}), 409

        user.email      = new_email
        user.otp_code   = None
        user.otp_expiry = None

    user.name  = new_name
    user.phone = new_phone
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Profil berhasil diperbarui!'}), 200


# ── POST /api/profile/photo ───────────────────────────────────────────────────

@profile_bp.route('/photo', methods=['POST'])
@jwt_required()
def update_photo():
    user = _get_user_or_404()
    file = request.files.get('photo')

    if not file or file.filename == '':
        return jsonify({'status': 'fail', 'message': 'File foto tidak ditemukan.'}), 400

    if not allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
        return jsonify({'status': 'fail', 'message': 'Format file tidak didukung (jpg/jpeg/png).'}), 400

    folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(folder, exist_ok=True)

    filename = f"avatar_{user.id}.jpg"
    file.save(os.path.join(folder, filename))

    user.photo_url = f"/static/img/avatars/{filename}"
    db.session.commit()

    return jsonify({
        'status':    'success',
        'message':   'Foto profil berhasil diperbarui.',
        'photo_url': user.photo_url,
    }), 200


# ── PATCH /api/profile/password ───────────────────────────────────────────────

@profile_bp.route('/password', methods=['PATCH'])
@jwt_required()
def change_password():
    user = _get_user_or_404()
    data = request.get_json() or {}

    old_pw  = data.get('password_lama', '')
    new_pw  = data.get('password_baru', '')
    confirm = data.get('konfirmasi_password', '')

    if not all([old_pw, new_pw, confirm]):
        return jsonify({'status': 'fail', 'message': 'Semua kolom kata sandi wajib diisi.'}), 400

    if not check_password_hash(user.password, old_pw):
        return jsonify({'status': 'fail', 'message': 'Kata sandi saat ini salah.'}), 401

    if new_pw != confirm:
        return jsonify({'status': 'fail', 'message': 'Konfirmasi kata sandi tidak cocok.'}), 400

    user.password = generate_password_hash(new_pw)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Kata sandi berhasil diperbarui.'}), 200


# ── Private helpers ───────────────────────────────────────────────────────────

def _get_user_or_404():
    user = User.query.get(get_jwt_identity())
    if not user:
        from flask import abort
        abort(404)
    return user


def _send_email_change_otp(user: User):
    otp = str(random.randint(100000, 999999))
    user.otp_code   = otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=5)
    db.session.commit()

    success = send_otp_email(user.name, user.email, otp)
    if not success:
        return jsonify({'status': 'fail', 'message': 'Gagal mengirim OTP.'}), 500

    return jsonify({
        'status':  'require_otp',
        'message': f'Kode OTP dikirim ke email lama ({user.email}).',
    }), 200