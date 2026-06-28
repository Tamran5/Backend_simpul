# app/routes/auth.py

import os
import random
import string
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity,
)
from werkzeug.security import generate_password_hash, check_password_hash
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.extensions import db
from app.models import User
from app.services.mail_service import send_verification_email, send_otp_email

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


# ── POST /api/auth/register ───────────────────────────────────────────────────

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}

    required = ['name', 'email', 'password', 'gender', 'religion']
    if not all(f in data for f in required):
        return jsonify({'status': 'fail', 'message': 'Data pendaftaran tidak lengkap.'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'status': 'fail', 'message': 'Email sudah terdaftar.'}), 409

    user = User(
        name         = data['name'],
        email        = data['email'],
        password     = generate_password_hash(data['password']),
        gender       = data['gender'],
        religion     = data['religion'],
        phone        = data.get('phone', ''),
        ktp_city     = data.get('ktp_city', ''),
        wedding_city = data.get('wedding_city', ''),
        is_out_of_town = bool(data.get('is_out_of_town', False)),
        is_foreigner   = bool(data.get('is_foreigner', False)),
        is_verified    = False,
    )
    user.generate_unique_code()
    db.session.add(user)
    db.session.commit()

    verify_url = f"{request.host_url.rstrip('/')}/auth/verify-email/{user.id}"
    send_verification_email(user.name, user.email, verify_url)

    return jsonify({
        'status':  'success',
        'message': 'Registrasi sukses! Silakan cek email untuk verifikasi akun.',
    }), 201


# ── POST /api/auth/login ──────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['POST'])
def login():
    data     = request.get_json() or {}
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'status': 'fail', 'message': 'Email dan password wajib diisi.'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({'status': 'fail', 'message': 'Email atau kata sandi salah.'}), 401

    if not user.is_verified:
        return jsonify({
            'status':  'fail',
            'message': 'Akun belum aktif. Silakan verifikasi email terlebih dahulu.',
        }), 403

    return jsonify({
        'status':        'success',
        'message':       'Login berhasil!',
        'access_token':  create_access_token(identity=str(user.id)),
        'refresh_token': create_refresh_token(identity=str(user.id)),
    }), 200


# ── POST /api/auth/refresh ────────────────────────────────────────────────────

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    new_token = create_access_token(identity=get_jwt_identity())
    return jsonify({'status': 'success', 'access_token': new_token}), 200


# ── POST /api/auth/google-login ───────────────────────────────────────────────

@auth_bp.route('/google-login', methods=['POST'])
def google_login():
    data  = request.get_json() or {}
    token = data.get('google_id_token')

    if not token:
        return jsonify({'status': 'fail', 'message': 'Token Google tidak ditemukan.'}), 400

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            current_app.config['GOOGLE_CLIENT_ID'],
        )
        email = idinfo['email']
    except ValueError:
        return jsonify({'status': 'fail', 'message': 'Token Google tidak valid atau kedaluwarsa.'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Kesalahan server: {str(e)}'}), 500

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({
            'status':  'fail',
            'message': 'Email belum terdaftar. Silakan daftar manual terlebih dahulu.',
        }), 404

    if not user.is_verified:
        user.is_verified = True
        db.session.commit()

    return jsonify({
        'status':        'success',
        'message':       'Login Google berhasil.',
        'access_token':  create_access_token(identity=str(user.id)),
        'refresh_token': create_refresh_token(identity=str(user.id)),
    }), 200


# ── POST /api/auth/forgot-password ───────────────────────────────────────────

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data  = request.get_json() or {}
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({'status': 'fail', 'message': 'Email wajib diisi.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'status': 'fail', 'message': 'Email tidak terdaftar.'}), 404

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # OTP masih aktif → jangan kirim ulang, hemat kuota SMTP
    if user.otp_code and user.otp_expiry and user.otp_expiry > now:
        sisa = int((user.otp_expiry - now).total_seconds())
        return jsonify({
            'status':            'success',
            'message':           f'OTP sebelumnya masih aktif (tersisa {max(1, round(sisa/60))} menit).',
            'remaining_seconds': sisa,
        }), 200

    otp = ''.join(random.choices(string.digits, k=6))
    user.otp_code   = otp
    user.otp_expiry = now + timedelta(minutes=5)
    db.session.commit()

    success = send_otp_email(user.name, user.email, otp)
    if not success:
        return jsonify({'status': 'fail', 'message': 'Gagal mengirim OTP. Coba lagi nanti.'}), 500

    return jsonify({
        'status':            'success',
        'message':           'Kode OTP dikirim ke email Anda.',
        'remaining_seconds': 300,
    }), 200


# ── POST /api/auth/reset-password ────────────────────────────────────────────

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data         = request.get_json() or {}
    email        = data.get('email', '').strip().lower()
    otp_input    = data.get('otp', '')
    new_password = data.get('new_password', '')

    if not all([email, otp_input, new_password]):
        return jsonify({'status': 'fail', 'message': 'Semua field wajib diisi.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'status': 'fail', 'message': 'Permintaan tidak valid.'}), 404

    if user.otp_code != otp_input or datetime.utcnow() > user.otp_expiry:
        return jsonify({'status': 'fail', 'message': 'OTP salah atau sudah kedaluwarsa.'}), 400

    user.password   = generate_password_hash(new_password)
    user.otp_code   = None
    user.otp_expiry = None
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Kata sandi berhasil diperbarui!'}), 200