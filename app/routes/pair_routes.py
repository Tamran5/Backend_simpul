from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, User

pair_bp = Blueprint('pair', __name__, url_prefix='/api/pair')

# --- 1. ENDPOINT: CEK STATUS SINKRONISASI & AMBIL KODE UNIKKU ---
@pair_bp.route('/status', methods=['GET'])
@jwt_required()
def get_pair_status():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"status": "fail", "message": "User tidak ditemukan"}), 404

        # Jaga-jaga: Jika unik kode user kosong, ciptakan detik ini juga
        if not user.unique_code:
            user.generate_unique_code()
            db.session.commit()

        partner_data = None
        if user.partner_id:
            partner = User.query.get(user.partner_id)
            if partner:
                partner_data = {
                    "id": partner.id,
                    "name": partner.name,
                    "email": partner.email,
                    "gender": partner.gender
                }

        return jsonify({
            "status": "success",
            "data": {
                "my_code": user.unique_code,
                "is_synced": user.is_synced,
                "sync_status": user.sync_status, # 'none', 'pending_sent', 'pending_received', 'synced'
                "partner": partner_data
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- 2. ENDPOINT: MENEMBAK KODE PASANGAN (REQUEST PAIRING) ---
@pair_bp.route('/request', methods=['POST'])
@jwt_required()
def request_pairing():
    try:
        user_a_id = get_jwt_identity()
        user_a = User.query.get(user_a_id)
        
        data = request.get_json() or {}
        target_code = data.get('unique_code', '').strip().upper()

        if not target_code:
            return jsonify({"status": "fail", "message": "Silakan masukkan kode pasangan."}), 400

        if user_a.unique_code == target_code:
            return jsonify({"status": "fail", "message": "Tidak dapat memasukkan kode milik sendiri!"}), 400

        if user_a.partner_id is not None or user_a.is_synced:
            return jsonify({"status": "fail", "message": "Akun Anda sudah terhubung dengan pasangan lain."}), 400

        # Cari calon pasangan di database
        user_b = User.query.filter_by(unique_code=target_code).first()
        if not user_b:
            return jsonify({"status": "fail", "message": "Kode pasangan tidak ditemukan di sistem."}), 404

        if user_b.partner_id is not None or user_b.is_synced:
            return jsonify({"status": "fail", "message": "Akun pasangan tersebut sudah terikat dengan orang lain."}), 400

        # IKAT KEDUA AKUN SECARA PENDING:
        user_a.partner_id = user_b.id
        user_a.sync_status = 'pending_sent'

        user_b.partner_id = user_a.id
        user_b.sync_status = 'pending_received'

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"Permintaan terkirim ke {user_b.name}! Menunggu persetujuan."
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# --- 3. ENDPOINT: MENJAWAB TEMBAKAN (ACCEPT / REJECT) ---
@pair_bp.route('/respond', methods=['POST'])
@jwt_required()
def respond_pairing():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        data = request.get_json() or {}
        action = data.get('action') # Cuma menerima kata: 'accept' atau 'reject'

        if user.sync_status != 'pending_received' or not user.partner_id:
            return jsonify({"status": "fail", "message": "Tidak ada ajakan pasangan yang masuk."}), 400

        partner = User.query.get(user.partner_id)

        if action == 'accept':
            user.is_synced = True
            user.sync_status = 'synced'
            
            if partner:
                partner.is_synced = True
                partner.sync_status = 'synced'
                
            db.session.commit()
            return jsonify({"status": "success", "message": "Selamat! Akun Anda dan pasangan resmi terhubung."}), 200

        elif action == 'reject':
            # Putuskan ikatan pending
            user.partner_id = None
            user.sync_status = 'none'
            user.is_synced = False
            
            if partner:
                partner.partner_id = None
                partner.sync_status = 'none'
                partner.is_synced = False
                
            db.session.commit()
            return jsonify({"status": "success", "message": "Ajakan pasangan berhasil ditolak."}), 200

        return jsonify({"status": "fail", "message": "Parameter action tidak valid."}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# --- 4. ENDPOINT: PUTUS HUBUNGAN (UNLINK / BATAL NIKAH) ---
@pair_bp.route('/unlink', methods=['POST'])
@jwt_required()
def unlink_pairing():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user.partner_id:
            return jsonify({"status": "fail", "message": "Anda tidak sedang terhubung dengan siapa pun."}), 400

        partner = User.query.get(user.partner_id)

        # Reset total ke titik nol
        user.partner_id = None
        user.sync_status = 'none'
        user.is_synced = False

        if partner:
            partner.partner_id = None
            partner.sync_status = 'none'
            partner.is_synced = False

        db.session.commit()
        return jsonify({"status": "success", "message": "Koneksi pasangan berhasil diputus."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500