# app/routes/vendors.py

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Vendor, FavoriteVendor

vendors_bp = Blueprint('vendors', __name__, url_prefix='/api/vendors')


# ── GET /api/vendors ──────────────────────────────────────────────────────────

@vendors_bp.route('', methods=['GET'])
@jwt_required()
def list_vendors():
    user_id  = get_jwt_identity()
    vendors  = Vendor.query.all()
    fav_ids  = {f.vendor_id for f in FavoriteVendor.query.filter_by(user_id=user_id).all()}
    return jsonify({
        'status': 'success',
        'data': [_vendor_dict(v, v.id in fav_ids) for v in vendors],
    }), 200


# ── GET /api/vendors/<id> ─────────────────────────────────────────────────────

@vendors_bp.route('/<int:vendor_id>', methods=['GET'])
@jwt_required()
def get_vendor(vendor_id):
    user_id = get_jwt_identity()
    vendor  = Vendor.query.get_or_404(vendor_id)
    is_fav  = FavoriteVendor.query.filter_by(user_id=user_id, vendor_id=vendor_id).first() is not None
    return jsonify({'status': 'success', 'data': _vendor_dict(vendor, is_fav)}), 200


# ── POST /api/vendors/<id>/favorite ──────────────────────────────────────────

@vendors_bp.route('/<int:vendor_id>/favorite', methods=['POST'])
@jwt_required()
def toggle_favorite(vendor_id):
    user_id = get_jwt_identity()
    Vendor.query.get_or_404(vendor_id)

    fav = FavoriteVendor.query.filter_by(user_id=user_id, vendor_id=vendor_id).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
        return jsonify({'status': 'success', 'is_favorite': False, 'message': 'Dihapus dari favorit.'}), 200

    db.session.add(FavoriteVendor(user_id=user_id, vendor_id=vendor_id))
    db.session.commit()
    return jsonify({'status': 'success', 'is_favorite': True, 'message': 'Ditambahkan ke favorit.'}), 201


# ── GET /api/vendors/favorites ────────────────────────────────────────────────

@vendors_bp.route('/favorites', methods=['GET'])
@jwt_required()
def list_favorites():
    user_id = get_jwt_identity()
    favs    = FavoriteVendor.query.filter_by(user_id=user_id).all()
    data    = [_vendor_dict(f.vendor, True) for f in favs if f.vendor]
    return jsonify({'status': 'success', 'data': data}), 200


# ── Private ───────────────────────────────────────────────────────────────────

def _vendor_dict(v: Vendor, is_favorite: bool = False) -> dict:
    d = v.to_dict()
    d['is_favorite'] = is_favorite
    return d