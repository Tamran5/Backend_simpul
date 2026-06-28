# app/routes/admin/api_articles.py
#
# REST API untuk manajemen artikel oleh admin web.
# Diproteksi dengan session (login_required), bukan JWT —
# karena dikonsumsi dari browser panel admin, bukan dari Flutter.

from datetime import datetime

from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models import Article
from .decorators import login_required

api_articles_bp = Blueprint('admin_articles', __name__, url_prefix='/articles')

# Batas panjang konten artikel
MIN_CONTENT_LEN = 200
MAX_CONTENT_LEN = 30_000


# ── GET /admin/articles/<id> ──────────────────────────────────────────────────

@api_articles_bp.route('/<int:article_id>', methods=['GET'])
@login_required
def get_article(article_id):
    article = Article.query.get_or_404(article_id)
    return jsonify({'status': 'success', 'data': _article_dict(article)}), 200


# ── POST /admin/articles ──────────────────────────────────────────────────────

@api_articles_bp.route('', methods=['POST'])
@login_required
def create_article():
    data = request.get_json() or {}

    judul    = data.get('judul', '').strip()
    kategori = data.get('kategori', '').strip()
    status   = data.get('status', '').strip()
    konten   = data.get('konten', '').strip()

    # Validasi wajib
    if not all([judul, kategori, status]):
        return jsonify({
            'status': 'fail',
            'message': 'Judul, kategori, dan status wajib diisi.',
        }), 400

    # Validasi panjang konten
    error = _validate_content_length(konten)
    if error:
        return jsonify({'status': 'fail', 'message': error}), 400

    article = Article(
        title           = judul,
        category        = kategori,
        status          = status,
        content         = konten,
        image_url       = data.get('image_url', ''),
        read_time       = data.get('read_time', '3 mnt'),
        target_religion = data.get('target_religion', 'Umum'),
        created_at      = datetime.now(),
    )
    db.session.add(article)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Artikel baru berhasil diterbitkan.'}), 201


# ── PUT /admin/articles/<id> ──────────────────────────────────────────────────

@api_articles_bp.route('/<int:article_id>', methods=['PUT'])
@login_required
def update_article(article_id):
    article = Article.query.get_or_404(article_id)
    data    = request.get_json() or {}

    # Validasi konten hanya jika dikirim
    konten_baru = data.get('konten')
    if konten_baru is not None:
        error = _validate_content_length(konten_baru.strip())
        if error:
            return jsonify({'status': 'fail', 'message': error}), 400
        article.content = konten_baru.strip()

    article.title           = data.get('judul',           article.title)
    article.category        = data.get('kategori',        article.category)
    article.status          = data.get('status',          article.status)
    article.image_url       = data.get('image_url',       article.image_url)
    article.read_time       = data.get('read_time',       article.read_time)
    article.target_religion = data.get('target_religion', article.target_religion)

    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Artikel berhasil diperbarui.'}), 200


# ── DELETE /admin/articles/<id> ───────────────────────────────────────────────

@api_articles_bp.route('/<int:article_id>', methods=['DELETE'])
@login_required
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Artikel berhasil dihapus.'}), 200


# ── Private helpers ───────────────────────────────────────────────────────────

def _article_dict(a: Article) -> dict:
    return {
        'id':              a.id,
        'judul':           a.title,
        'kategori':        a.category,
        'status':          a.status,
        'konten':          a.content,
        'image_url':       a.image_url or '',
        'read_time':       a.read_time or '3 mnt',
        'target_religion': a.target_religion or 'Umum',
    }


def _validate_content_length(konten: str) -> str | None:
    """Return pesan error atau None jika valid."""
    if len(konten) < MIN_CONTENT_LEN:
        return (
            f"Konten terlalu pendek ({len(konten)} karakter). "
            f"Minimal {MIN_CONTENT_LEN} karakter."
        )
    if len(konten) > MAX_CONTENT_LEN:
        return (
            f"Konten melebihi batas ({len(konten)} karakter). "
            f"Maksimal {MAX_CONTENT_LEN:,} karakter."
        )
    return None