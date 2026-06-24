import os
import random
import string
from flask import Blueprint, request, jsonify, current_app, session
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, create_refresh_token, jwt_required
from flask_mail import Message
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app import db, mail
from app.models import Admin, Article, User, Bookmark
from datetime import datetime, timedelta
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from dotenv import load_dotenv

api_bp = Blueprint('api', __name__, url_prefix='/api')

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# --- [POST] LOGIN: Generate Token JWT ---
@api_bp.route('/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"status": "fail", "message": "Email dan password wajib diisi."}), 400

    admin = Admin.query.filter_by(email=email).first()

    if admin and admin.check_password(password):
        # Membuat Token Akses Digital dengan masa berlaku (Identity diisi ID admin berupa string)
        token_jwt = create_access_token(identity=str(admin.id))
        
        # Tetap set session untuk kebutuhan navigasi halaman HTML di browser
        session['admin_id'] = admin.id
        session['admin_name'] = admin.name
        
        return jsonify({
            "status": "success",
            "message": "Login berhasil, mengalihkan...",
            "token": token_jwt, # <-- Token dikirim ke Client (Browser / Flutter)
            "data": {"nama": admin.name, "email": admin.email}
        }), 200
    
    return jsonify({"status": "fail", "message": "Email atau password salah."}), 401


# --- [PUT] UPDATE PROFIL: Diproteksi JWT ---
@api_bp.route('/admin/profile', methods=['PUT'])
@jwt_required() # <-- Hanya bisa diakses jika menyertakan Token JWT yang sah
def api_update_profile():
    # Mengambil ID Admin langsung dari Token JWT yang dikirim client
    current_admin_id = get_jwt_identity()
    admin = Admin.query.get(current_admin_id)

    if not admin:
        return jsonify({"status": "fail", "message": "Admin tidak ditemukan."}), 404

    nama_baru = request.form.get('nama_lengkap')
    file_foto = request.files.get('foto_profil')

    if nama_baru:
        admin.name = nama_baru
        session['admin_name'] = nama_baru

    if file_foto and file_foto.filename != '':
        ekstensi = os.path.splitext(file_foto.filename)[1].lower()
        if ekstensi in ['.jpg', '.jpeg', '.png']:
            nama_file_aman = f"avatar_{admin.id}.jpg"
            folder_simpan = os.path.join(current_app.root_path, 'static', 'img', 'avatars')
            
            if not os.path.exists(folder_simpan):
                os.makedirs(folder_simpan)
                
            file_foto.save(os.path.join(folder_simpan, nama_file_aman))
            admin.profile_pic = nama_file_aman
        else:
            return jsonify({"status": "fail", "message": "Format gambar tidak didukung!"}), 400

    db.session.commit()
    return jsonify({
        "status": "success",
        "message": "Profil Anda berhasil diperbarui.",
        "data": {"nama": admin.name, "foto": admin.profile_pic}
    }), 200


# --- [PATCH] UBAH PASSWORD: Diproteksi JWT ---
@api_bp.route('/admin/password', methods=['PATCH'])
@jwt_required() # <-- Hanya bisa diakses jika menyertakan Token JWT yang sah
def api_ubah_password():
    current_admin_id = get_jwt_identity()
    admin = Admin.query.get(current_admin_id)

    if not admin:
        return jsonify({"status": "fail", "message": "Admin tidak ditemukan."}), 404

    data = request.get_json() or {}
    password_lama = data.get('password_lama')
    password_baru = data.get('password_baru')
    konfirmasi_password = data.get('konfirmasi_password')

    if not password_lama or not password_baru or not konfirmasi_password:
        return jsonify({"status": "fail", "message": "Semua kolom kata sandi wajib diisi."}), 400

    if not admin.check_password(password_lama):
        return jsonify({"status": "fail", "message": "Kata sandi saat ini salah."}), 401

    if password_baru != konfirmasi_password:
        return jsonify({"status": "fail", "message": "Konfirmasi kata sandi baru tidak cocok."}), 400

    admin.set_password(password_baru)
    db.session.commit()
    
    return jsonify({"status": "success", "message": "Kata sandi akun berhasil diperbarui."}), 200


    
@api_bp.route('/auth/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and check_password_hash(user.password, password):
        if not user.is_verified:
            return jsonify({
                "status": "fail", 
                "message": "Akun Anda belum aktif. Silakan lakukan verifikasi email terlebih dahulu!"
            }), 403 # 403 Forbidden (Dilarang masuk)
            
        # KONVERSI IDENTITY KE STRING (Rekomendasi Keamanan Flask-JWT-Extended)
        user_identity = str(user.id)
        
        #BUAT ACCESS TOKEN & REFRESH TOKEN SEKALIGUS
        access_token = create_access_token(identity=user_identity)
        refresh_token = create_refresh_token(identity=user_identity)
        
        return jsonify({
            "status": "success", 
            "message": "Login berhasil!",
            "access_token": access_token,   # Berlaku singkat (Short-lived) untuk akses data
            "refresh_token": refresh_token  # Berlaku lama (Long-lived) untuk perpanjang token
        }), 200
        
    return jsonify({"status": "fail", "message": "Email atau kata sandi salah."}), 401

@api_bp.route('/auth/google-login', methods=['POST'])
def google_login():
    # Ekstrak data dari request frontend terlebih dahulu
    data = request.get_json()
    token = data.get('google_id_token')

    if not token:
        return jsonify({"status": "fail", "message": "Token Google tidak ditemukan"}), 400

    try:
        # 1. Verifikasi keaslian token langsung ke server Google
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)

        # 2. Ekstrak email dari Google
        email = idinfo['email']

        print(f"\n[DEBUG] Email dari Google: '{email}'")

        # 3. Cek apakah email ini sudah terdaftar di database kita
        user = User.query.filter_by(email=email).first()

        if user:
            print(f"[DEBUG] User ditemukan di DB: {user.email}")
        else:
            print("[DEBUG] User TIDAK DITEMUKAN di tabel MySQL!")
        # KONDISI JIKA BELUM DAFTAR MANUAL
        if not user:
            return jsonify({
                "status": "fail", 
                "message": "Email ini belum terdaftar di aplikasi Simpul. Silakan daftar akun secara manual terlebih dahulu!"
            }), 404 # 404 Not Found

        # KONDISI JIKA SUDAH TERDAFTAR (LOGIN BERHASIL)
        # Konversi identity ke string (Best practice JWT)
        user_identity = str(user.id)
        
        # 4. Buat tiket masuk (JWT) Simpul
        access_token = create_access_token(identity=user_identity)
        refresh_token = create_refresh_token(identity=user_identity)

        # Jika sebelumnya user daftar manual tapi belum verifikasi email, 
        # kita otomatis anggap terverifikasi karena berhasil masuk via Google
        if not user.is_verified:
            user.is_verified = True
            db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Login Google berhasil",
            "access_token": access_token,
            "refresh_token": refresh_token
        }), 200

    except ValueError:
        # Menangkap error jika Token Google dimanipulasi oleh peretas / sudah kedaluwarsa
        return jsonify({"status": "fail", "message": "Token Google tidak valid atau sudah kedaluwarsa"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": f"Terjadi kesalahan di pelayan server: {str(e)}"}), 500
    
@api_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True) #Dikunci khusus hanya menerima REFRESH TOKEN
def refresh_session():
    # Ambil ID user dari refresh token yang dikirim oleh Flutter
    current_user_id = get_jwt_identity()
    
    # Buatkan Access Token baru yang segar
    new_access_token = create_access_token(identity=current_user_id)
    
    return jsonify({
        "status": "success",
        "access_token": new_access_token
    }), 200

# ==========================================================
# [MOBILE] MOBILE REGISTER 
# ==========================================================
@api_bp.route('/auth/register', methods=['POST'])
def register_user():
    data = request.get_json()
    
    # Validasi input wajib
    required_fields = ['name', 'email', 'password', 'gender', 'religion']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"status": "fail", "message": "Data tidak lengkap."}), 400
        
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"status": "fail", "message": "Email sudah terdaftar."}), 400
        
    hashed_password = generate_password_hash(data['password'])
    
    new_user = User(
        name=data['name'],
        email=data['email'],
        password=hashed_password,
        gender=data['gender'],
        religion=data['religion'],
        phone=data.get('phone', ''),
        is_verified=False
    )

    new_user.generate_unique_code()
    
    db.session.add(new_user)
    db.session.commit()
    
    
    try:
        base_url = request.host_url.rstrip('/')
        link_verifikasi = f"{base_url}/api/auth/verify-email/{new_user.id}"
        
        msg = Message(
            subject="Verifikasi Akun Simpul Wedding Planner Anda",
            recipients=[new_user.email]
        )
        
        # Isi pesan email (bisa dibikin teks rapi)
        msg.body = f"""Halo {new_user.name},

Terima kasih telah mendaftarkan akun Anda di Simpul Wedding Planner!
Satu langkah lagi sebelum Anda dapat menggunakan aplikasi kami, silakan klik tautan di bawah ini untuk mengaktifkan akun Anda:

{link_verifikasi}

Jika Anda tidak merasa mendaftar di aplikasi kami, silakan abaikan email ini.
Salam hangat,
Tim Developer Simpul
"""
        # Eksekusi kirim email lewat server SMTP Gmail
        mail.send(msg)
        
    except Exception as e:
        print(f"Gagal mengirim email: {str(e)}")
        # Akun tetap terbuat di database, tapi ada log error di terminal jika SMTP gagal
    
    return jsonify({
        "status": "success", 
        "message": "Registrasi sukses! Silakan cek email Anda untuk melakukan verifikasi akun sebelum login."
    }), 201



# ==========================================================
# [ADMIN WEB] READ ALL USER: Admin memantau daftar user mobile
# ==========================================================
@api_bp.route('/admin/users', methods=['GET'])
@jwt_required()
def admin_get_users():
    users = User.query.all()
    output = []
    
    for user in users:
        output.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "gender": user.gender,
            "religion": user.religion,
            "is_verified": user.is_verified
        })
        
    return jsonify({"status": "success", "data": output}), 200


# ==========================================================
# [ADMIN WEB] DELETE USER: Admin menghapus akun bermasalah
# ==========================================================
@api_bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({"status": "success", "message": "Akun pengguna berhasil dihapus dari sistem."}), 200

@api_bp.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"status": "fail", "message": "Email tidak terdaftar di sistem kami."}), 404
        
    # Generate 6 digit angka acak
    otp = str(random.randint(100000, 999999))
    
    # Simpan ke database dengan masa berlaku 5 menit ke depan
    user.otp_code = otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=5)
    db.session.commit()
    
    # Kirim OTP beneran ke Gmail User
    try:
        msg = Message(
            subject="[Simpul] Kode OTP Reset Kata Sandi Anda",
            recipients=[user.email]
        )
        msg.body = f"""Halo {user.name},

Kami menerima permintaan untuk mereset kata sandi akun Simpul Anda.
Berikut adalah kode OTP verifikasi Anda:

 {otp} 

Kode ini bersifat rahasia dan hanya berlaku selama 5 menit. Jangan bagikan kode ini kepada siapa pun.

Salam hangat,
Tim Developer Simpul
"""
        mail.send(msg)
        return jsonify({"status": "success", "message": "Kode OTP berhasil dikirim ke email Anda."}), 200
        
    except Exception as e:
        print(f"Gagal kirim email: {str(e)}")
        return jsonify({"status": "fail", "message": "Gagal mengirim email OTP. Coba lagi nanti."}), 500


# ENDPOINT: VERIFIKASI OTP & UPDATE PASSWORD BARU
@api_bp.route('/auth/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    otp_input = data.get('otp')
    new_password = data.get('new_password')
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"status": "fail", "message": "Permintaan tidak valid."}), 404
        
    # Validasi apakah OTP cocok dan belum kedaluwarsa
    if user.otp_code != otp_input or datetime.utcnow() > user.otp_expiry:
        return jsonify({"status": "fail", "message": "Kode OTP salah atau telah kedaluwarsa!"}), 400
        
    # Enkripsi password baru dan bersihkan kolom OTP di database
    user.password = generate_password_hash(new_password)
    user.otp_code = None
    user.otp_expiry = None
    db.session.commit()
    
    return jsonify({"status": "success", "message": "Kata sandi berhasil diperbarui! Silakan login kembali."}), 200

@api_bp.route('/auth/profile', methods=['GET'])
@jwt_required() 
def get_user_profile():
    try:
        # 1. Ambil ID Pengguna dari token JWT yang dikirim di Header oleh Flutter
        current_user_id = get_jwt_identity()
        
        # 2. Cari baris data pengguna di database MySQL berdasarkan ID tersebut
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                "status": "fail", 
                "message": "Data pengguna tidak ditemukan di sistem."
            }), 404
            
        # 3. Kembalikan data profil asli secara dinamis ke aplikasi mobile
        return jsonify({
            "status": "success",
            "message": "Berhasil memuat data profil pengguna.",
            "data": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "gender": user.gender,
                "religion": user.religion,
                "is_synced": user.is_synced,
                "partner_name": user.partner_name if user.partner_name else "",
                "wedding_date": user.wedding_date if user.wedding_date else "",
                "my_code": user.unique_code,
                "sync_status": user.sync_status,
                "partner_name": user.partner_name if user.partner_name else "",
            }
        }), 200

    except Exception as e:
        print(f"Error pada sistem profile: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": "Terjadi kesalahan internal pada server."
        }), 500
    
@api_bp.route('/auth/update-profile', methods=['POST'])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    data = request.get_json()
    new_name = data.get('name')
    new_email = data.get('email', '').strip().lower()
    new_phone = data.get('phone')
    otp_input = data.get('otp') 
    
    if not user:
        return jsonify({"status": "fail", "message": "Pengguna tidak ditemukan."}), 404

    # LOGIKA UTAMA: VALIDASI JIKA USER MENGUBAH EMAIL
    if new_email != user.email.lower():
        # STEP A: Jika user belum memasukkan OTP, kirim OTP ke email SEBELUMNYA
        if not otp_input:
            otp = str(random.randint(100000, 999999))
            user.otp_code = otp
            user.otp_expiry = datetime.utcnow() + timedelta(minutes=5)
            db.session.commit()
            
            # Kirim Email OTP ke email lama
            try:
                msg = Message("[Simpul] Verifikasi Perubahan Email", recipients=[user.email])
                msg.body = f"""Halo {user.name},

Anda mendeteksi adanya permintaan perubahan alamat email pada akun Simpul Anda.
Untuk mengizinkan perubahan ini, silakan masukkan kode OTP di bawah ke dalam aplikasi:

 {otp} 

Kode ini dikirim ke email Anda saat ini untuk memastikan keamanan akun Anda.
"""
                mail.send(msg)
                return jsonify({
                    "status": "require_otp",
                    "message": f"Kode OTP verifikasi telah dikirim ke email sebelumnya ({user.email})."
                }), 200
            except Exception as e:
                return jsonify({"status": "fail", "message": "Gagal mengirim OTP ke email lama."}), 500
        
        # STEP B: Jika user sudah memasukkan OTP, lakukan validasi kecocokan
        if user.otp_code != otp_input or datetime.utcnow() > user.otp_expiry:
            return jsonify({"status": "fail", "message": "Kode OTP salah atau telah kedaluwarsa!"}), 400
            
        # Cek apakah email baru sudah dipakai orang lain di database
        email_check = User.query.filter(User.email == new_email, User.id != user.id).first()
        if email_check:
            return jsonify({"status": "fail", "message": "Email baru sudah digunakan oleh akun lain."}), 400
            
        # OTP Valid! Izinkan pembaruan email baru
        user.email = new_email
        user.otp_code = None
        user.otp_expiry = None

    # Update data umum (Nama & Nomor Telepon)
    user.name = new_name
    user.phone = new_phone
    db.session.commit()
    
    return jsonify({
        "status": "success", 
        "message": "Profil Anda berhasil diperbarui!"
    }), 200

# 1. Endpoint Mengirim Undangan Sinkronisasi
@api_bp.route('/auth/connect-partner', methods=['POST'])
@jwt_required()
def connect_partner():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    partner_code = request.get_json().get('partner_code', '').upper()
    
    if user.unique_code == partner_code:
        return jsonify({"status": "fail", "message": "Tidak dapat memasukkan kode diri sendiri."}), 400
        
    target_partner = User.query.filter_by(unique_code=partner_code).first()
    if not target_partner:
        return jsonify({"status": "fail", "message": "Kode pasangan tidak ditemukan."}), 404
        
    if target_partner.sync_status != 'none':
        return jsonify({"status": "fail", "message": "Pasangan tersebut sudah terhubung dengan orang lain atau memiliki permintaan aktif."}), 400

    # Kunci relasi dan set status ke PENDING
    user.partner_id = target_partner.id
    user.sync_status = 'pending_sent'
    
    target_partner.partner_id = user.id
    target_partner.sync_status = 'pending_received'
    
    db.session.commit()
    return jsonify({"status": "success", "message": "Permintaan berhasil dikirim. Menunggu persetujuan pasangan."}), 200

# 2. Endpoint Merespons Undangan (Terima/Tolak)
@api_bp.route('/auth/respond-partner', methods=['POST'])
@jwt_required()
def respond_partner():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    action = request.get_json().get('action') # 'accept' atau 'reject'
    
    if user.sync_status != 'pending_received':
        return jsonify({"status": "fail", "message": "Tidak ada permintaan sinkronisasi."}), 400
        
    partner = User.query.get(user.partner_id)
    
    if action == 'accept':
        user.sync_status = 'synced'
        partner.sync_status = 'synced'
        user.partner_name = partner.name # Set nama pasangan
        partner.partner_name = user.name
        db.session.commit()
        return jsonify({"status": "success", "message": "Sinkronisasi berhasil!"}), 200
    else:
        # Jika ditolak, bersihkan relasinya
        user.partner_id = None
        user.sync_status = 'none'
        partner.partner_id = None
        partner.sync_status = 'none'
        db.session.commit()
        return jsonify({"status": "success", "message": "Permintaan ditolak."}), 200

@api_bp.route('/mobile/articles', methods=['GET'])
@jwt_required() 
def mobile_get_articles():
    # Hanya ambil artikel yang sudah 'Diterbitkan'
    articles = Article.query.filter_by(status='Diterbitkan').order_by(Article.created_at.desc()).all()
    
    article_list = []
    for art in articles:
        article_list.append({
            "id": art.id,
            "judul": art.title,
            "kategori": art.category,
            "image_url": art.image_url if art.image_url else "",
            "read_time": art.read_time if art.read_time else "3 mnt",
            "target_religion": art.target_religion if art.target_religion else "Umum",
            "konten": art.content
        })
        
    return jsonify({
        "status": "success",
        "data": article_list
    }), 200

@api_bp.route('/mobile/bookmarks/toggle/<int:article_id>', methods=['POST'])
@jwt_required()
def toggle_bookmark(article_id):
    current_user_id = get_jwt_identity()
    
    # Cek apakah bookmark sudah ada
    bookmark = Bookmark.query.filter_by(user_id=current_user_id, article_id=article_id).first()
    
    if bookmark:
        # Jika sudah ada, hapus dari bookmark
        db.session.delete(bookmark)
        db.session.commit()
        return jsonify({"status": "success", "message": "Artikel dihapus dari simpanan", "is_bookmarked": False}), 200
    else:
        # Jika belum ada, tambahkan ke bookmark
        new_bookmark = Bookmark(user_id=current_user_id, article_id=article_id)
        db.session.add(new_bookmark)
        db.session.commit()
        return jsonify({"status": "success", "message": "Artikel berhasil disimpan", "is_bookmarked": True}), 201

# --- [GET] AMBIL SEMUA BOOKMARK USER ---
@api_bp.route('/mobile/bookmarks', methods=['GET'])
@jwt_required()
def get_user_bookmarks():
    current_user_id = get_jwt_identity()
    
    # Ambil data bookmark milik user, urutkan dari yang terbaru disimpan
    bookmarks = Bookmark.query.filter_by(user_id=current_user_id).order_by(Bookmark.created_at.desc()).all()
    
    article_list = []
    for bm in bookmarks:
        art = Article.query.get(bm.article_id)
        if art:
            article_list.append({
                "id": art.id,
                "judul": art.title,
                "kategori": art.category,
                "image_url": art.image_url if art.image_url else "",
                "read_time": art.read_time if art.read_time else "3 mnt",
                "target_religion": art.target_religion if art.target_religion else "Umum",
                "konten": art.content
            })
            
    return jsonify({"status": "success", "data": article_list}), 200