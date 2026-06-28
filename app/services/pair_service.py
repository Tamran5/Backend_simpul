# app/services/pair_service.py
#
# Logika bisnis untuk pairing antar user.
# Route hanya memanggil fungsi di sini — tidak ada query DB di route.

from app.extensions import db
from app.models import User, Notification


def get_pair_info(user: User) -> dict:
    """
    Kembalikan status pair + info pasangan.
    sync_status: none | pending_sent | pending_received | synced
    """
    if user.sync_status == 'synced' and user.partner_id:
        partner = User.query.get(user.partner_id)
        return {
            'is_synced':   True,
            'sync_status': 'synced',
            'partner': _partner_dict(partner) if partner else None,
        }

    if user.sync_status == 'pending_sent' and user.partner_id:
        partner = User.query.get(user.partner_id)
        return {
            'is_synced':   False,
            'sync_status': 'pending_sent',
            'partner': _partner_dict(partner) if partner else None,
        }

    if user.sync_status == 'pending_received' and user.partner_id:
        partner = User.query.get(user.partner_id)
        return {
            'is_synced':   False,
            'sync_status': 'pending_received',
            'partner': _partner_dict(partner) if partner else None,
        }

    return {'is_synced': False, 'sync_status': 'none', 'partner': None}


def send_pair_request(user: User, partner_code: str) -> tuple[dict, int]:
    """
    Kirim permintaan sinkronisasi ke user dengan unique_code = partner_code.
    Return (response_dict, http_status).
    """
    if user.unique_code == partner_code:
        return {'status': 'fail', 'message': 'Tidak dapat memasukkan kode diri sendiri.'}, 400

    if user.sync_status != 'none':
        return {'status': 'fail', 'message': 'Kamu sudah terhubung atau memiliki permintaan aktif.'}, 400

    target = User.query.filter_by(unique_code=partner_code).first()
    if not target:
        return {'status': 'fail', 'message': 'Kode pasangan tidak ditemukan.'}, 404

    if target.sync_status != 'none':
        return {
            'status': 'fail',
            'message': 'Pasangan tersebut sudah terhubung dengan orang lain.',
        }, 400

    user.partner_id   = target.id
    user.sync_status  = 'pending_sent'
    target.partner_id = user.id
    target.sync_status = 'pending_received'

    # Notifikasi in-app ke penerima
    _push_notif(
        user_id    = target.id,
        title      = f'{user.name} mengajakmu terhubung 💌',
        body       = 'Buka Simpul untuk menerima atau menolak undangan.',
        notif_type = 'pair',
    )

    db.session.commit()
    return {'status': 'success', 'message': 'Permintaan berhasil dikirim.'}, 200


def respond_pair_request(user: User, action: str) -> tuple[dict, int]:
    """
    Terima ('accept') atau tolak ('reject') permintaan pair yang masuk.
    """
    if user.sync_status != 'pending_received':
        return {'status': 'fail', 'message': 'Tidak ada permintaan sinkronisasi masuk.'}, 400

    partner = User.query.get(user.partner_id)
    if not partner:
        return {'status': 'fail', 'message': 'Data pasangan tidak ditemukan.'}, 404

    if action == 'accept':
        user.sync_status    = 'synced'
        partner.sync_status = 'synced'
        user.partner_name    = partner.name
        partner.partner_name = user.name

        _push_notif(
            user_id    = partner.id,
            title      = f'{user.name} menerima undanganmu 💕',
            body       = 'Kalian sekarang bisa merencanakan pernikahan bersama!',
            notif_type = 'pair',
        )
        db.session.commit()
        return {'status': 'success', 'message': 'Sinkronisasi berhasil!'}, 200

    # action == 'reject'
    user.partner_id     = None
    user.sync_status    = 'none'
    partner.partner_id  = None
    partner.sync_status = 'none'
    db.session.commit()
    return {'status': 'success', 'message': 'Permintaan ditolak.'}, 200


def disconnect_pair(user: User) -> tuple[dict, int]:
    """Putuskan sinkronisasi yang sudah aktif."""
    if user.sync_status != 'synced' or not user.partner_id:
        return {'status': 'fail', 'message': 'Tidak ada sinkronisasi aktif.'}, 400

    partner = User.query.get(user.partner_id)

    user.partner_id     = None
    user.sync_status    = 'none'
    user.partner_name   = None

    if partner:
        partner.partner_id   = None
        partner.sync_status  = 'none'
        partner.partner_name = None
        _push_notif(
            user_id    = partner.id,
            title      = 'Sinkronisasi diputus',
            body       = f'{user.name} memutuskan sinkronisasi akun.',
            notif_type = 'pair',
        )

    db.session.commit()
    return {'status': 'success', 'message': 'Sinkronisasi berhasil diputus.'}, 200


# ── Private helpers ───────────────────────────────────────────────────────────

def _partner_dict(partner: User) -> dict:
    return {
        'id':        partner.id,
        'name':      partner.name,
        'photo_url': partner.photo_url or '',
    }


def _push_notif(user_id: int, title: str, body: str, notif_type: str = 'info') -> None:
    from app.models import Notification  # avoid circular import at module level
    db.session.add(Notification(
        user_id    = user_id,
        title      = title,
        body       = body,
        notif_type = notif_type,
    ))