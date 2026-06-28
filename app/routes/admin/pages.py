import os
from datetime import datetime

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash, current_app, jsonify
)
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Admin, Article, User, Vendor
from app.utils.helpers import allowed_file
from .decorators import login_required
from app.services import pair_service

pages_bp = Blueprint('admin_pages', __name__)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@pages_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('admin/dashboard.html')


# ── Vendor ────────────────────────────────────────────────────────────────────

@pages_bp.route('/vendor')
@login_required
def vendor_page():
    vendors = Vendor.query.all()
    return render_template('admin/katalog_vendor.html', vendors=vendors)


# ── Manajemen Pengguna ────────────────────────────────────────────────────────

@pages_bp.route('/manajemen-pengguna')
@login_required
def manajemen_pengguna():
    users            = User.query.all()
    total_users      = User.query.count()
    verified_users   = User.query.filter_by(is_verified=True).count()
    unverified_users = User.query.filter_by(is_verified=False).count()
    new_users        = User.query.order_by(User.id.desc()).limit(5).count()

    
    for u in users:
        pair_info = pair_service.get_pair_info(u)
        u.is_synced = pair_info.get('is_synced', False)
        u.partner_name = ''
        if u.is_synced and pair_info.get('partner'):
            u.partner_name = pair_info['partner'].get('name', '')

    return render_template(
        'admin/manajemen_pengguna.html',
        users            = users,
        total_users      = total_users,
        verified_users   = verified_users,
        unverified_users = unverified_users,
        new_users        = new_users,
    )

# ── Edukasi ───────────────────────────────────────────────────────────────────

@pages_bp.route('/edukasi')
@login_required
def edukasi():
    articles = Article.query.order_by(Article.id.desc()).all()
    return render_template('admin/edukasi.html', articles=articles)


# ── Pengaturan ────────────────────────────────────────────────────────────────

@pages_bp.route('/pengaturan')
@login_required
def pengaturan():
    admin = Admin.query.get(session['admin_id'])
    return render_template('admin/pengaturan.html', admin=admin)


@pages_bp.route('/pengaturan/update-profil', methods=['POST'])
@login_required
def update_profil():
    admin     = Admin.query.get(session['admin_id'])
    nama_baru = request.form.get('nama_lengkap', '').strip()
    file_foto = request.files.get('foto_profil')

    if nama_baru:
        admin.name             = nama_baru
        session['admin_name']  = nama_baru

    if file_foto and file_foto.filename:
        if not allowed_file(file_foto.filename, {'jpg', 'jpeg', 'png', 'gif'}):
            return jsonify({
                'status': 'fail',
                'message': 'Format file tidak didukung! Gunakan JPG, JPEG, PNG, atau GIF.',
            }), 400

        folder = os.path.join(current_app.root_path, 'static', 'img', 'avatars')
        os.makedirs(folder, exist_ok=True)

        ext      = os.path.splitext(file_foto.filename)[1].lower()
        filename = secure_filename(f"avatar_{admin.id}{ext}")
        file_foto.save(os.path.join(folder, filename))
        admin.foto_profil = filename

    db.session.commit()
    return jsonify({
        'status':  'success',
        'message': 'Profil berhasil diperbarui.',
        'data': {
            'nama': admin.name,
            'foto_url': url_for('static', filename=f'img/avatars/{admin.foto_profil}') if admin.foto_profil else None,
        },
    }), 200


@pages_bp.route('/pengaturan/ubah-password', methods=['POST'])
@login_required
def ubah_password():
    admin               = Admin.query.get(session['admin_id'])
    password_lama       = request.form.get('password_lama', '')
    password_baru       = request.form.get('password_baru', '')
    konfirmasi_password = request.form.get('konfirmasi_password', '')

    if not admin.check_password(password_lama):
        flash('Kata sandi saat ini salah!', 'error')
        return redirect(url_for('admin_pages.pengaturan'))

    if password_baru != konfirmasi_password:
        flash('Konfirmasi kata sandi baru tidak cocok!', 'error')
        return redirect(url_for('admin_pages.pengaturan'))

    admin.set_password(password_baru)
    db.session.commit()
    flash('Kata sandi berhasil diperbarui!', 'success')
    return redirect(url_for('admin_pages.pengaturan'))