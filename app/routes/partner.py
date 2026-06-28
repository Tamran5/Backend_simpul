# app/routes/partner.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import User
from app.services import pair_service

partner_bp = Blueprint('partner', __name__, url_prefix='/api/partner')


# ── POST /api/partner/connect ─────────────────────────────────────────────────

@partner_bp.route('/connect', methods=['POST'])
@jwt_required()
def connect():
    user         = User.query.get_or_404(get_jwt_identity())
    partner_code = (request.get_json() or {}).get('partner_code', '').strip().upper()

    if not partner_code:
        return jsonify({'status': 'fail', 'message': 'Kode pasangan wajib diisi.'}), 400

    result, status = pair_service.send_pair_request(user, partner_code)
    return jsonify(result), status


# ── POST /api/partner/respond ─────────────────────────────────────────────────

@partner_bp.route('/respond', methods=['POST'])
@jwt_required()
def respond():
    user   = User.query.get_or_404(get_jwt_identity())
    action = (request.get_json() or {}).get('action', '').strip()

    if action not in ('accept', 'reject'):
        return jsonify({'status': 'fail', 'message': 'Action harus "accept" atau "reject".'}), 400

    result, status = pair_service.respond_pair_request(user, action)
    return jsonify(result), status


# ── DELETE /api/partner/disconnect ────────────────────────────────────────────

@partner_bp.route('/disconnect', methods=['DELETE'])
@jwt_required()
def disconnect():
    user           = User.query.get_or_404(get_jwt_identity())
    result, status = pair_service.disconnect_pair(user)
    return jsonify(result), status


# ── GET /api/partner/status ───────────────────────────────────────────────────

@partner_bp.route('/status', methods=['GET'])
@jwt_required()
def status():
    user      = User.query.get_or_404(get_jwt_identity())
    pair_info = pair_service.get_pair_info(user)
    return jsonify({
        'status': 'success',
        'data': {
            'my_code':     user.unique_code,
            'is_synced':   pair_info['is_synced'],
            'sync_status': pair_info['sync_status'],
            'partner':     pair_info['partner'],
        },
    }), 200