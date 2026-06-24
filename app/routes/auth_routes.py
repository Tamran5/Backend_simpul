from flask import Blueprint, render_template, redirect, url_for, session, jsonify
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

# --- JALUR TAMPILAN: HALAMAN LOGIN ---
@auth_bp.route('/login', methods=['GET'])
def login():
    # Jika admin terdeteksi sudah login, langsung alihkan ke dashboard (tidak perlu login lagi)
    if 'admin_id' in session:
        return redirect(url_for('admin.dashboard'))
        
    return render_template('auth/login.html')


# --- JALUR AKSI: LOGOUT / KELUAR ---
@auth_bp.route('/logout', methods=['GET'])
def logout():
    session.clear()
    
    # Kembalikan admin ke halaman login utama
    return redirect(url_for('auth.login'))


@auth_bp.route('/auth/verify-email/<int:user_id>', methods=['GET'])
def verify_email(user_id):
    # Ambil data user berdasarkan ID, jika tidak ada langsung return 404
    user = User.query.get_or_404(user_id)
    
    if user.is_verified:
        return """
        <div style="text-align: center; margin-top: 100px; font-family: sans-serif;">
            <h2 style="color: #596E63;">Akun Sudah Aktif</h2>
            <p style="color: #666666;">Akun ini sudah terverifikasi sebelumnya. Silakan langsung login di aplikasi Simpul.</p>
        </div>
        """, 200
        
    # Ubah status akun menjadi aktif di database MySQL
    user.is_verified = True
    db.session.commit()
    
    # Tampilan sukses yang estetik saat diklik di browser
    return """
    <div style="text-align: center; margin-top: 100px; font-family: sans-serif;">
        <div style="color: #596E63; font-size: 50px; margin-bottom: 20px;">✓</div>
        <h2 style="color: #596E63; font-weight: bold;">Verifikasi Berhasil!</h2>
        <p style="color: #666666; font-size: 16px; line-height: 1.6;">
            Akun Simpul Anda dengan email <b>{}</b> telah berhasil diaktifkan.<br>
            Silakan kembali ke aplikasi mobile untuk masuk ke akun Anda.
        </p>
    </div>
    """.format(user.email), 200