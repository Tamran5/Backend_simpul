# app/routes/articles.py

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Article, Bookmark

articles_bp = Blueprint('articles', __name__, url_prefix='/api/articles')


# ── GET /api/articles ─────────────────────────────────────────────────────────

@articles_bp.route('', methods=['GET'])
@jwt_required()
def list_articles():
    articles = (
        Article.query
        .filter_by(status='Diterbitkan')
        .order_by(Article.created_at.desc())
        .all()
    )
    user_id = get_jwt_identity()
    saved   = {b.article_id for b in Bookmark.query.filter_by(user_id=user_id).all()}

    return jsonify({
        'status': 'success',
        'data': [_article_dict(a, a.id in saved) for a in articles],
    }), 200


# ── POST /api/articles/<id>/bookmark ─────────────────────────────────────────

@articles_bp.route('/<int:article_id>/bookmark', methods=['POST'])
@jwt_required()
def toggle_bookmark(article_id):
    user_id  = get_jwt_identity()
    bookmark = Bookmark.query.filter_by(user_id=user_id, article_id=article_id).first()

    if bookmark:
        db.session.delete(bookmark)
        db.session.commit()
        return jsonify({'status': 'success', 'is_bookmarked': False, 'message': 'Dihapus dari simpanan.'}), 200

    Article.query.get_or_404(article_id)
    db.session.add(Bookmark(user_id=user_id, article_id=article_id))
    db.session.commit()
    return jsonify({'status': 'success', 'is_bookmarked': True, 'message': 'Artikel disimpan.'}), 201


# ── GET /api/articles/bookmarks ───────────────────────────────────────────────

@articles_bp.route('/bookmarks', methods=['GET'])
@jwt_required()
def list_bookmarks():
    user_id   = get_jwt_identity()
    bookmarks = Bookmark.query.filter_by(user_id=user_id).order_by(Bookmark.created_at.desc()).all()
    articles  = [_article_dict(bm.article, True) for bm in bookmarks if bm.article]
    return jsonify({'status': 'success', 'data': articles}), 200


# ── Private ───────────────────────────────────────────────────────────────────

def _article_dict(a: Article, is_bookmarked: bool = False) -> dict:
    return {
        'id':              a.id,
        'judul':           a.title,
        'kategori':        a.category,
        'image_url':       a.image_url or '',
        'read_time':       a.read_time or '3 mnt',
        'target_religion': a.target_religion or 'Umum',
        'konten':          a.content,
        'is_bookmarked':   is_bookmarked,
    }