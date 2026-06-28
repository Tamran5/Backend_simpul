# app/models.py

import string
import random
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN
# ─────────────────────────────────────────────────────────────────────────────

class Admin(db.Model):
    __tablename__ = 'admins'

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    foto_profil   = db.Column(db.String(255), nullable=True, default='default_avatar.png')

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.email}>'


# ─────────────────────────────────────────────────────────────────────────────
# USER
# ─────────────────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'

    # Data utama
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    email       = db.Column(db.String(120), unique=True, nullable=False)
    password    = db.Column(db.String(200), nullable=False)
    gender      = db.Column(db.String(20), nullable=False)
    religion    = db.Column(db.String(30), nullable=False)
    phone       = db.Column(db.String(20), nullable=True)
    photo_url   = db.Column(db.String(500), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)

    # Profil legalitas nikah
    ktp_city       = db.Column(db.String(100), nullable=True)
    wedding_city   = db.Column(db.String(100), nullable=True)
    is_out_of_town = db.Column(db.Boolean, default=False)
    is_foreigner   = db.Column(db.Boolean, default=False)

    # OTP
    otp_code   = db.Column(db.String(6),  nullable=True)
    otp_expiry = db.Column(db.DateTime,   nullable=True)

    # Sinkronisasi pasangan
    unique_code  = db.Column(db.String(8), unique=True, nullable=True)
    partner_id   = db.Column(db.Integer,   nullable=True)
    partner_name = db.Column(db.String(100), nullable=True)
    sync_status  = db.Column(db.String(20), default='none')  # none | pending_sent | pending_received | synced

    face_embedding    = db.Column(db.JSON,    nullable=True)   # Vektor 512-dim
    face_registered   = db.Column(db.Boolean, default=False)   # Sudah setup wajah?
    face_registered_at = db.Column(db.DateTime, nullable=True)

    # Relasi
    wedding       = db.relationship('WeddingPlan',  backref='user', uselist=False, cascade='all, delete-orphan')
    tasks         = db.relationship('Task',         backref='user', lazy='dynamic',  cascade='all, delete-orphan')
    legal_docs    = db.relationship('LegalDocument',backref='user', lazy='dynamic',  cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic',  cascade='all, delete-orphan',
                                    order_by='Notification.created_at.desc()')
    bookmarks     = db.relationship('Bookmark',     backref='user', lazy='dynamic',  cascade='all, delete-orphan')

    def generate_unique_code(self) -> None:
        """Buat kode unik 6 karakter (huruf kapital + angka), pastikan tidak bentrok."""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(chars, k=6))
            if not User.query.filter_by(unique_code=code).first():
                self.unique_code = code
                break

    def __repr__(self):
        return f'<User {self.email}>'


# ─────────────────────────────────────────────────────────────────────────────
# WEDDING PLAN
# ─────────────────────────────────────────────────────────────────────────────

class WeddingPlan(db.Model):
    __tablename__ = 'wedding_plans'

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    wedding_date = db.Column(db.Date,     nullable=True)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<WeddingPlan user_id={self.user_id} date={self.wedding_date}>'


# ─────────────────────────────────────────────────────────────────────────────
# TASK (To-Do)
# ─────────────────────────────────────────────────────────────────────────────

class Task(db.Model):
    __tablename__ = 'tasks'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title      = db.Column(db.String(255), nullable=False)
    is_done    = db.Column(db.Boolean, default=False)
    category   = db.Column(db.String(50), default='umum')  # 'legal' | 'umum'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Task {self.title} done={self.is_done}>'


# ─────────────────────────────────────────────────────────────────────────────
# LEGAL DOCUMENT
# ─────────────────────────────────────────────────────────────────────────────

class LegalDocument(db.Model):
    __tablename__ = 'legal_documents'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doc_code   = db.Column(db.String(10), nullable=False)   # N1 | N2 | N3 | N4
    level      = db.Column(db.String(50), nullable=False)   # Kelurahan | KUA
    is_done    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<LegalDocument {self.doc_code} user_id={self.user_id}>'


# ─────────────────────────────────────────────────────────────────────────────
# NOTIFICATION
# ─────────────────────────────────────────────────────────────────────────────

class Notification(db.Model):
    __tablename__ = 'notifications'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title      = db.Column(db.String(255), nullable=False)
    body       = db.Column(db.Text, nullable=True)
    notif_type = db.Column(db.String(50), default='info')   # info | pair | task | legal
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Notification {self.title} user_id={self.user_id}>'


# ─────────────────────────────────────────────────────────────────────────────
# ARTICLE
# ─────────────────────────────────────────────────────────────────────────────

class Article(db.Model):
    __tablename__ = 'articles'

    id              = db.Column(db.Integer, primary_key=True)
    title           = db.Column(db.String(200), nullable=False)
    category        = db.Column(db.String(100), nullable=False)
    status          = db.Column(db.String(50), default='Draft', nullable=False)
    content         = db.Column(db.Text, nullable=True)
    image_url       = db.Column(db.String(255), nullable=True)
    read_time       = db.Column(db.String(20), nullable=True)
    target_religion = db.Column(db.String(50), default='Umum')
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    bookmarks = db.relationship('Bookmark', backref='article', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Article {self.title}>'


# ─────────────────────────────────────────────────────────────────────────────
# BOOKMARK
# ─────────────────────────────────────────────────────────────────────────────

class Bookmark(db.Model):
    __tablename__ = 'bookmarks'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'article_id', name='_user_article_bm_uc'),
    )

    def __repr__(self):
        return f'<Bookmark user={self.user_id} article={self.article_id}>'


# ─────────────────────────────────────────────────────────────────────────────
# VENDOR
# ─────────────────────────────────────────────────────────────────────────────

class Vendor(db.Model):
    __tablename__ = 'vendors'

    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(100), nullable=False)
    category       = db.Column(db.String(50),  nullable=False)
    location       = db.Column(db.String(255), nullable=False)
    price_start    = db.Column(db.String(100), nullable=False)
    rating         = db.Column(db.Float, default=0.0)
    image_url      = db.Column(db.String(255), nullable=True)
    whatsapp       = db.Column(db.String(20),  nullable=True)
    philosophy     = db.Column(db.Text,        nullable=True)
    portfolio_urls = db.Column(db.JSON,        nullable=True)
    packages       = db.Column(db.JSON,        nullable=True)

    def to_dict(self) -> dict:
        return {
            'id':             self.id,
            'name':           self.name,
            'category':       self.category,
            'location':       self.location,
            'price':          self.price_start,
            'rating':         float(self.rating),
            'image_url':      self.image_url or '',
            'philosophy':     self.philosophy or '',
            'portfolio_urls': self.portfolio_urls or [],
            'packages':       self.packages or [],
            'whatsapp':       self.whatsapp or '',
            'is_favorite':    False,  # di-override di route jika perlu
        }

    def __repr__(self):
        return f'<Vendor {self.name}>'


# ─────────────────────────────────────────────────────────────────────────────
# FAVORITE VENDOR
# ─────────────────────────────────────────────────────────────────────────────

class FavoriteVendor(db.Model):
    __tablename__ = 'favorite_vendors'

    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id',    ondelete='CASCADE'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id',  ondelete='CASCADE'), nullable=False)

    vendor = db.relationship('Vendor', backref=db.backref('favorited_by', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'vendor_id', name='_user_vendor_fav_uc'),
    )

    def __repr__(self):
        return f'<FavoriteVendor user={self.user_id} vendor={self.vendor_id}>'
    
class JourneyStepProgress(db.Model):
    __tablename__ = 'journey_step_progress'
 
    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    step_key = db.Column(db.String(80), nullable=False)  # contoh: 'rt_rw', 'kua_daftar_nikah', dst
 
    is_done        = db.Column(db.Boolean, default=False)
    document_path  = db.Column(db.String(500), nullable=True)
    document_name  = db.Column(db.String(255), nullable=True)
 
    # Flag agar notifikasi "step bimbingan terbuka" hanya dikirim sekali,
    # tidak berulang setiap kali endpoint /journey dipanggil.
    guidance_notified = db.Column(db.Boolean, default=False)
 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
 
    user = db.relationship('User', backref=db.backref('journey_progress', lazy='dynamic',
                                                        cascade='all, delete-orphan'))
 
    __table_args__ = (
        db.UniqueConstraint('user_id', 'step_key', name='_user_step_uc'),
    )
 
    def to_dict(self) -> dict:
        return {
            'step_key':      self.step_key,
            'is_done':       self.is_done,
            'document_path': self.document_path or '',
            'document_name': self.document_name or '',
        }
 
    def __repr__(self):
        return f'<JourneyStepProgress user={self.user_id} step={self.step_key} done={self.is_done}>'
 