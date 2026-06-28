# app/routes/admin/api_vendors.py
#
# REST API untuk manajemen vendor oleh admin web.
# Diproteksi session (login_required).

from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models import Vendor
from .decorators import login_required

api_vendors_bp = Blueprint('admin_vendors', __name__, url_prefix='/admin/vendors')


# ── GET /admin/vendors/<id> ───────────────────────────────────────────────────

@api_vendors_bp.route('/<int:vendor_id>', methods=['GET'])
@login_required
def get_vendor(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    return jsonify({'status': 'success', 'data': vendor.to_dict()}), 200


# ── POST /admin/vendors ───────────────────────────────────────────────────────

@api_vendors_bp.route('', methods=['POST'])
@login_required
def create_vendor():
    data = request.get_json() or {}

    name        = data.get('name', '').strip()
    category    = data.get('category', '').strip()
    location    = data.get('location', '').strip()
    price_start = data.get('price')

    if not all([name, category, location, price_start]):
        return jsonify({
            'status':  'fail',
            'message': 'Nama, kategori, lokasi, dan harga awal wajib diisi.',
        }), 400

    try:
        vendor = Vendor(
            name           = name,
            category       = category,
            location       = location,
            price_start    = price_start,
            whatsapp       = data.get('whatsapp', ''),
            rating         = float(data.get('rating', 0.0)),
            image_url      = data.get('image_url', ''),
            philosophy     = data.get('philosophy', ''),
            portfolio_urls = data.get('portfolio_urls', []),
            packages       = data.get('packages', []),
        )
        db.session.add(vendor)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Vendor baru berhasil ditambahkan.'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ── PUT /admin/vendors/<id> ───────────────────────────────────────────────────

@api_vendors_bp.route('/<int:vendor_id>', methods=['PUT'])
@login_required
def update_vendor(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    data   = request.get_json() or {}

    try:
        vendor.name           = data.get('name',           vendor.name)
        vendor.category       = data.get('category',       vendor.category)
        vendor.location       = data.get('location',       vendor.location)
        vendor.price_start    = data.get('price',          vendor.price_start)
        vendor.image_url      = data.get('image_url',      vendor.image_url)
        vendor.philosophy     = data.get('philosophy',     vendor.philosophy)
        vendor.whatsapp       = data.get('whatsapp',       vendor.whatsapp)
        vendor.portfolio_urls = data.get('portfolio_urls', vendor.portfolio_urls)
        vendor.packages       = data.get('packages',       vendor.packages)

        if 'rating' in data:
            vendor.rating = float(data['rating'])

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Data vendor berhasil diperbarui.'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ── DELETE /admin/vendors/<id> ────────────────────────────────────────────────

@api_vendors_bp.route('/<int:vendor_id>', methods=['DELETE'])
@login_required
def delete_vendor(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    try:
        db.session.delete(vendor)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Vendor berhasil dihapus.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500