import string, random
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    foto_profil = db.Column(db.String(255), nullable=True, default='default_avatar.png')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class User(db.Model):
    __tablename__ = 'users'
    
    # --- DATA UTAMA ---
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    gender = db.Column(db.String(20), nullable=False)      
    religion = db.Column(db.String(30), nullable=False)   
    is_verified = db.Column(db.Boolean, default=False)      # Default: Belum Terverifikasi
    phone = db.Column(db.String(20), nullable=True)
    
    # --- KEAMANAN & OTP ---
    otp_code = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)

    # --- PROFIL & JADWAL PERNIKAHAN ---
    is_synced = db.Column(db.Boolean, default=False)
    partner_name = db.Column(db.String(100), nullable=True)
    wedding_date = db.Column(db.String(50), nullable=True)

    # 🔗 --- SISTEM SINKRONISASI PASANGAN (BARU) ---
    unique_code = db.Column(db.String(8), unique=True, nullable=True) # Kode undangan
    partner_id = db.Column(db.Integer, nullable=True)                 # ID akun pasangan di database
    sync_status = db.Column(db.String(20), default='none')            # Status: none, pending_sent, pending_received, synced

    def generate_unique_code(self):
        """Menghasilkan 6 karakter kode unik (Kombinasi huruf kapital & angka)"""
        chars = string.ascii_uppercase + string.digits
        self.unique_code = ''.join(random.choice(chars) for _ in range(6))

    def __repr__(self):
        return f'<User {self.email}>'
    
class Article(db.Model):
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='Draft', nullable=False) 
    content = db.Column(db.Text, nullable=True)
    
    image_url = db.Column(db.String(255), nullable=True)
    read_time = db.Column(db.String(20), nullable=True) 
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi balik (opsional, mempermudah query)
    bookmarks = db.relationship('Bookmark', backref='article', lazy=True, cascade="all, delete-orphan")

    target_religion = db.Column(db.String(50), default='Umum')

    def __repr__(self):
        return f'<Article {self.title}>'


class Bookmark(db.Model):
    __tablename__ = 'bookmarks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Bookmark User:{self.user_id} - Article:{self.article_id}>'
