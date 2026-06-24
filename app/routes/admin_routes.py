import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime
from app.extensions import db
from app.models import Admin, Article, User
from werkzeug.utils import secure_filename
import functools

admin_bp = Blueprint('admin', __name__)

# Decorator Pengaman Halaman
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('admin/dashboard.html')

@admin_bp.route('/katalog-vendor')
@login_required
def katalog_vendor():
    return render_template('admin/katalog_vendor.html')

@admin_bp.route('/manajemen-pengguna', methods=['GET'])
def manajemen_pengguna():
    # 1. Ambil semua data pengguna dari database MySQL
    users = User.query.all()
    
    # 2. Hitung statistik secara dinamis berdasarkan database
    total_users = User.query.count()
    verified_users = User.query.filter_by(is_verified=True).count()
    unverified_users = User.query.filter_by(is_verified=False).count()
    
    # Simulasi hitung pengguna baru (misal: ID besar/terakhir) atau bisa disamakan sementara
    new_users = User.query.order_by(User.id.desc()).limit(5).count() 

    # 3. Lempar semua data ke file HTML template kamu
    return render_template(
        'admin/manajemen_pengguna.html', 
        users=users, 
        total_users=total_users, 
        verified_users=verified_users, 
        unverified_users=unverified_users,
        new_users=new_users
    )

@admin_bp.route('/edukasi')
@login_required
def edukasi():
    data_artikel = Article.query.order_by(Article.id.desc()).all()
    return render_template('admin/edukasi.html', articles=data_artikel)

@admin_bp.route('/pengaturan', methods=['GET'])
@login_required
def pengaturan():
    admin = Admin.query.get(session['admin_id'])
    return render_template('admin/pengaturan.html', admin=admin)

@admin_bp.route('/pengaturan/update-profil', methods=['POST'])
@login_required
def update_profil():
    admin = Admin.query.get(session['admin_id'])
    nama_baru = request.form.get('nama_lengkap')
    file_foto = request.files.get('foto_profil') 
    
    # 1. Proses Update Nama Lengkap
    if nama_baru:
        admin.name = nama_baru
        session['admin_name'] = nama_baru

    # 2. Proses Unggah Foto Profil jika ada file yang dipilih
    if file_foto and file_foto.filename != '':
        # Validasi ekstensi file yang diizinkan
        ekstensi = os.path.splitext(file_foto.filename)[1].lower()
        if ekstensi in ['.jpg', '.jpeg', '.png', '.gif']:
            
            # Buat nama file unik agar tidak bentrok (contoh: avatar_1.jpg)
            nama_file_aman = secure_filename(f"avatar_{admin.id}{ekstensi}")
            
            # Tentukan path penyimpanan: app/static/img/avatars/
            folder_simpan = os.path.join(current_app.root_path, 'static', 'img', 'avatars')
            
            # Buat foldernya otomatis jika belum ada di dalam proyek
            if not os.path.exists(folder_simpan):
                os.makedirs(folder_simpan)
                
            # Simpan file gambar fisik ke folder proyek
            path_lengkap = os.path.join(folder_simpan, nama_file_aman)
            file_foto.save(path_lengkap)
            
            # Simpan nama file-nya saja ke kolom database MySQL
            admin.foto_profil = nama_file_aman
        else:
            flash('Format file tidak didukung! Gunakan JPG, JPEG, atau PNG.', 'error')
            return redirect(url_for('admin.pengaturan'))

    db.session.commit()
    flash('Profil Anda berhasil diperbarui.', 'success')
    return redirect(url_for('admin.pengaturan'))

# PUSH DATA: Validasi dan enkripsi password baru
@admin_bp.route('/pengaturan/ubah-password', methods=['POST'])
@login_required
def ubah_password():
    admin = Admin.query.get(session['admin_id'])
    password_lama = request.form.get('password_lama')
    password_baru = request.form.get('password_baru')
    konfirmasi_password = request.form.get('konfirmasi_password')

    if not admin.check_password(password_lama):
        flash('Kata sandi saat ini salah!', 'error')
        return redirect(url_for('admin.pengaturan'))

    if password_baru != konfirmasi_password:
        flash('Konfirmasi kata sandi baru tidak cocok!', 'error')
        return redirect(url_for('admin.pengaturan'))

    admin.set_password(password_baru)
    db.session.commit()
    flash('Kata sandi berhasil diperbarui!', 'success')
    
    return redirect(url_for('admin.pengaturan'))

# --- [GET] READ SINGLE: Mengambil 1 data artikel utuh berdasarkan ID ---
@admin_bp.route('/articles/<int:article_id>', methods=['GET'])
@login_required # 👈 UBAH JADI INI
def api_get_article(article_id):
    article = Article.query.get(article_id)
    if not article:
        return jsonify({"status": "fail", "message": "Artikel tidak ditemukan."}), 404
        
    return jsonify({
        "status": "success",
        "data": {
            "id": article.id,
            "judul": article.title,
            "kategori": article.category,
            "status": article.status,
            "konten": article.content,
            "image_url": article.image_url,
            "read_time": article.read_time,
            "target_religion": article.target_religion
        }
    }), 200

# --- [POST] CREATE: Tambah Artikel Baru ---
@admin_bp.route('/articles', methods=['POST'])
@login_required # 👈 UBAH DI SINI
def api_create_article():
    data = request.get_json() or {}
    judul = data.get('judul')
    kategori = data.get('kategori')
    status = data.get('status')
    konten = data.get('konten', '') or '' 
    target_religion = data.get('target_religion', 'Umum')
    
    # Tangkap data gambar dan waktu baca
    image_url = data.get('image_url', '')
    read_time = data.get('read_time', '3 mnt')

    if not judul or not kategori or not status:
        return jsonify({"status": "fail", "message": "Judul, kategori, dan status wajib diisi."}), 400

    # Validasi Batas Panjang Konten Artikel Baru
    if len(konten) < 200:
        return jsonify({
            "status": "fail", 
            "message": f"Isi konten terlalu pendek ({len(konten)} karakter). Minimal adalah 200 karakter agar informatif."
        }), 400

    if len(konten) > 30000:
        return jsonify({
            "status": "fail", 
            "message": f"Isi konten melebihi batas ({len(konten)} karakter). Maksimal adalah 30.000 karakter."
        }), 400

    new_article = Article(
        title=judul,
        category=kategori,
        status=status,
        content=konten,
        image_url=image_url, 
        read_time=read_time, 
        target_religion=target_religion,
        created_at=datetime.now()
    )
    db.session.add(new_article)
    db.session.commit()

    return jsonify({"status": "success", "message": "Artikel baru berhasil diterbitkan."}), 201


# --- [PUT] UPDATE: Mengubah Isi Artikel ---
@admin_bp.route('/articles/<int:article_id>', methods=['PUT'])
@login_required # 👈 UBAH DI SINI
def api_update_article(article_id):
    article = Article.query.get(article_id)
    if not article:
        return jsonify({"status": "fail", "message": "Artikel tidak ditemukan."}), 404

    data = request.get_json() or {}
    
    # Ambil konten baru jika ada di dalam request data
    konten_baru = data.get('konten')

    # Validasi Batas Panjang Konten Hanya Jika Konten Diperbarui/Diubah
    if konten_baru is not None:
        if len(konten_baru) < 200:
            return jsonify({
                "status": "fail", 
                "message": f"Isi konten baru terlalu pendek ({len(konten_baru)} karakter). Minimal adalah 200 karakter."
            }), 400

        if len(konten_baru) > 30000:
            return jsonify({
                "status": "fail", 
                "message": f"Isi konten baru melebihi batas ({len(konten_baru)} karakter). Maksimal adalah 30.000 karakter."
            }), 400
        
        # Jika lolos validasi, perbarui field konten
        article.content = konten_baru

    # Perbarui field lainnya
    article.title = data.get('judul', article.title)
    article.category = data.get('kategori', article.category)
    article.status = data.get('status', article.status)
    
    # PERBAIKAN: Masukkan target_religion ke model agar tersimpan
    article.target_religion = data.get('target_religion', article.target_religion)
    
    # Perbarui gambar dan waktu baca (Gunakan data lama jika form JSON tidak mengirimkannya)
    article.image_url = data.get('image_url', article.image_url)
    article.read_time = data.get('read_time', article.read_time)

    db.session.commit()
    return jsonify({"status": "success", "message": "Artikel berhasil diperbarui."}), 200


# --- [DELETE] DELETE: Menghapus Artikel ---
@admin_bp.route('/articles/<int:article_id>', methods=['DELETE'])
@login_required # 👈 UBAH DI SINI
def api_delete_article(article_id):
    article = Article.query.get(article_id)
    if not article:
        return jsonify({"status": "fail", "message": "Artikel tidak ditemukan."}), 404

    db.session.delete(article)
    db.session.commit()
    return jsonify({"status": "success", "message": "Artikel berhasil dihapus secara permanen."}), 200
