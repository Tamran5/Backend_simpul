import os
from flask import Blueprint, jsonify, send_from_directory, abort, render_template, current_app

from app.extensions import db
from app.models import User, JourneyStepProgress
from .decorators import login_required
from app.services import journey_service, pair_service 

api_users_bp = Blueprint('admin_users', __name__, url_prefix='/admin/users')


# ── GET /admin/users ──────────────────────────────────────────────────────────

@api_users_bp.route('', methods=['GET'])
@login_required
def list_users():
    users = User.query.order_by(User.id.desc()).all()
    return jsonify({
        'status': 'success',
        'data': [_user_dict(u) for u in users],
    }), 200

@api_users_bp.route('/<int:user_id>', methods=['GET'])
@login_required
def get_user_detail(user_id):
    user = User.query.get_or_404(user_id)
    pair_info = pair_service.get_pair_info(user)

    partner_name = ''
    if pair_info.get('is_synced') and pair_info.get('partner'):
        partner_name = pair_info['partner'].get('name', '')

    return jsonify({
        'status': 'success',
        'data': {
            **_user_dict(user),
            'is_synced':    pair_info.get('is_synced', False),
            'partner_name': partner_name,
        },
    }), 200

# ── DELETE /admin/users/<id> ──────────────────────────────────────────────────

@api_users_bp.route('/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Akun pengguna berhasil dihapus.'}), 200


# ── Private ───────────────────────────────────────────────────────────────────

def _user_dict(u: User) -> dict:
    return {
        'id':          u.id,
        'name':        u.name,
        'email':       u.email,
        'gender':      u.gender,
        'religion':    u.religion,
        'is_verified': u.is_verified,
        'sync_status': u.sync_status,
    }




@api_users_bp.route('/dokumen')
@login_required
def dokumen_page():
    documents, summary = _get_all_documents()
    return render_template('admin/dokumen.html', documents=documents, **summary)


@api_users_bp.route('/dokumen/<int:progress_id>/file')
@login_required
def view_document_file(progress_id):
    row = JourneyStepProgress.query.get_or_404(progress_id)
    if not row.document_path:
        abort(404)

    # document_path tersimpan seperti: /uploads/journey_docs/<user_id>/<file>
    upload_root = os.path.join(current_app.root_path, '..', 'uploads')
    relative = row.document_path.replace('/uploads/', '', 1)
    return send_from_directory(upload_root, relative)


def _get_all_documents():
    """Gabungkan JourneyStepProgress dengan definisi step (judul, lembaga)
    karena daftar step bergantung pada profil masing-masing user
    (agama, gender, dll), bukan kolom statis di database."""
    rows = JourneyStepProgress.query.filter(
        JourneyStepProgress.document_path.isnot(None)
    ).order_by(JourneyStepProgress.updated_at.desc()).all()

    users_cache = {}
    documents = []

    for row in rows:
        user = users_cache.get(row.user_id)
        if user is None:
            user = User.query.get(row.user_id)
            users_cache[row.user_id] = user
        if not user:
            continue

        steps = journey_service.get_steps_for_user(user)
        step_def = next((s for s in steps if s['step_key'] == row.step_key), None)
        if not step_def:
            continue

        documents.append({
            'progress_id':        row.id,
            'user_name':          user.name,
            'user_email':         user.email,
            'step_title':         step_def['title'],
            'target_institution': step_def['target_institution'],
            'document_name':      row.document_name,
            'uploaded_at':        row.updated_at,
        })

    summary = {
        'total_documents': len(documents),
        'total_users_with_docs': len(users_cache),
    }
    return documents, summary