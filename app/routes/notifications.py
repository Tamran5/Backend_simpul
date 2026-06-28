# app/routes/notifications.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Notification

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


# ── GET /api/notifications/unread-count ──────────────────────────────────────

@notifications_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def unread_count():
    count = Notification.query.filter_by(
        user_id=get_jwt_identity(), is_read=False
    ).count()
    return jsonify({'data': {'count': count}}), 200


# ── GET /api/notifications ────────────────────────────────────────────────────

@notifications_bp.route('', methods=['GET'])
@jwt_required()
def list_notifications():
    limit  = min(int(request.args.get('limit', 20)), 50)
    offset = int(request.args.get('offset', 0))

    items = (
        Notification.query
        .filter_by(user_id=get_jwt_identity())
        .order_by(Notification.created_at.desc())
        .limit(limit).offset(offset)
        .all()
    )
    return jsonify({
        'data': [_notif_dict(n) for n in items]
    }), 200


# ── PATCH /api/notifications/read-all ────────────────────────────────────────

@notifications_bp.route('/read-all', methods=['PATCH'])
@jwt_required()
def mark_all_read():
    Notification.query.filter_by(
        user_id=get_jwt_identity(), is_read=False
    ).update({'is_read': True})
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Semua notifikasi ditandai sudah dibaca.'}), 200


# ── PATCH /api/notifications/<id>/read ───────────────────────────────────────

@notifications_bp.route('/<int:notif_id>/read', methods=['PATCH'])
@jwt_required()
def mark_one_read(notif_id):
    notif = Notification.query.filter_by(
        id=notif_id, user_id=get_jwt_identity()
    ).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({'status': 'success'}), 200


# ── Private ───────────────────────────────────────────────────────────────────

def _notif_dict(n: Notification) -> dict:
    return {
        'id':         n.id,
        'title':      n.title,
        'body':       n.body or '',
        'type':       n.notif_type,
        'is_read':    n.is_read,
        'created_at': n.created_at.isoformat(),
    }