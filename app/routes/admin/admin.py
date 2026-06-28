# app/routes/admin.py
#
# Endpoint ini diproteksi JWT admin (bukan user mobile).
# Gunakan token admin dari POST /api/admin/login.

import os
from flask import Blueprint, request, jsonify, current_app, session
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import Admin, User
from app.utils.helpers import allowed_file

admin_bp = Blueprint('admin', __name__, url_prefix='/api')


# ── POST /api/admin/login ─────────────────────────────────────────────────────

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    data     = request.get_json() or {}
    email    = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'status': 'fail', 'message': 'Email dan password wajib diisi.'}), 400

    admin = Admin.query.filter_by(email=email).first()
    if not admin or not admin.check_password(password):
        return jsonify({'status': 'fail', 'message': 'Email atau password salah.'}), 401

    session['admin_id']   = admin.id
    session['admin_name'] = admin.name

    return jsonify({
        'status':  'success',
        'message': 'Login admin berhasil.',
        'token':   create_access_token(identity=str(admin.id)),
        'data':    {'nama': admin.name, 'email': admin.email},
    }), 200


# ── PUT /api/admin/profile ────────────────────────────────────────────────────

@admin_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_admin_profile():
    admin    = Admin.query.get_or_404(get_jwt_identity())
    new_name = request.form.get('nama_lengkap')
    file     = request.files.get('foto_profil')

    if new_name:
        admin.name        = new_name
        session['admin_name'] = new_name

    if file and file.filename:
        if not allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
            return jsonify({'status': 'fail', 'message': 'Format gambar tidak didukung.'}), 400

        folder   = current_app.config['UPLOAD_FOLDER']
        os.makedirs(folder, exist_ok=True)
        filename = f"avatar_{admin.id}.jpg"
        file.save(os.path.join(folder, filename))
        admin.profile_pic = filename

    db.session.commit()
    return jsonify({
        'status':  'success',
        'message': 'Profil admin berhasil diperbarui.',
        'data':    {'nama': admin.name, 'foto': admin.profile_pic},
    }), 200


# ── PATCH /api/admin/password ─────────────────────────────────────────────────

# @admin_bp.route('/password', methods=['PATCH'])
# @jwt_required()
# def change_admin_password():
#     admin = Admin.query.get_or_404(get_jwt_identity())
#     data  = request.get_json() or {}

#     old_pw  = data.get('password_lama', '')
#     new_pw  = data.get('password_baru', '')
#     confirm = data.get('konfirmasi_password', '')

#     if not all([old_pw, new_pw, confirm]):
#         return jsonify({'status': 'fail', 'message': 'Semua kolom kata sandi wajib diisi.'}), 400

#     if not admin.check_password(old_pw):
#         return jsonify({'status': 'fail', 'message': 'Kata sandi saat ini salah.'}), 401

#     if new_pw != confirm:
#         return jsonify({'status': 'fail', 'message': 'Konfirmasi kata sandi tidak cocok.'}), 400

#     admin.set_password(new_pw)
#     db.session.commit()
#     return jsonify({'status': 'success', 'message': 'Kata sandi admin berhasil diperbarui.'}), 200


# ── GET /api/admin/users ──────────────────────────────────────────────────────

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    users = User.query.all()
    return jsonify({
        'status': 'success',
        'data': [
            {
                'id':          u.id,
                'name':        u.name,
                'email':       u.email,
                'gender':      u.gender,
                'religion':    u.religion,
                'is_verified': u.is_verified,
                'sync_status': u.sync_status,
            }
            for u in users
        ],
    }), 200


# ── DELETE /api/admin/users/<id> ──────────────────────────────────────────────

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Akun pengguna berhasil dihapus.'}), 200