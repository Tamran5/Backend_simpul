# app/routes/admin/auth_web.py
#
# Route berbasis SESSION untuk admin web panel:
#   - Halaman login & logout admin
#   - Verifikasi email user mobile (diklik dari link email)
#
# Berbeda dari app/routes/auth.py yang melayani Flutter via JWT.

from flask import Blueprint, render_template, redirect, url_for, session

from app.extensions import db
from app.models import User

auth_web_bp = Blueprint('auth_web', __name__)


# ── GET /login ────────────────────────────────────────────────────────────────

@auth_web_bp.route('/login')
def login():
    # Jika sudah login, langsung ke dashboard — tidak perlu login ulang
    if 'admin_id' in session:
        return redirect(url_for('admin_pages.dashboard'))
    return render_template('auth/login.html')


# ── GET /logout ───────────────────────────────────────────────────────────────

@auth_web_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_web.login'))


# ── GET /auth/verify-email/<user_id> ─────────────────────────────────────────
# Link ini dikirim via email ke user mobile setelah register.
# Saat diklik di browser, akun langsung diaktifkan.

@auth_web_bp.route('/auth/verify-email/<int:user_id>')
def verify_email(user_id):
    user = User.query.get_or_404(user_id)

    if user.is_verified:
        return _render_page(
            icon  = '📋',
            title = 'Akun Sudah Aktif',
            body  = 'Akun ini sudah terverifikasi sebelumnya. Silakan langsung login di aplikasi Simpul.',
            color = '#8A8A8A',
        ), 200

    user.is_verified = True
    db.session.commit()

    return _render_page(
        icon  = '✓',
        title = 'Verifikasi Berhasil!',
        body  = (
            f'Akun Simpul Anda dengan email <b>{user.email}</b> telah berhasil diaktifkan.<br>'
            'Silakan kembali ke aplikasi mobile untuk masuk ke akun Anda.'
        ),
        color = '#3D6B5F',
    ), 200


# ── Private helper ────────────────────────────────────────────────────────────

def _render_page(icon: str, title: str, body: str, color: str) -> str:
    """Render halaman konfirmasi sederhana tanpa template file."""
    return f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} — Simpul</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #F5F6F5; margin: 0; padding: 0; }}
            .card {{
                max-width: 480px; margin: 100px auto; background: white;
                border-radius: 20px; padding: 48px 40px; text-align: center;
                box-shadow: 0 4px 24px rgba(0,0,0,0.06);
            }}
            .icon  {{ font-size: 52px; margin-bottom: 16px; }}
            h2     {{ color: {color}; font-size: 22px; margin: 0 0 12px; }}
            p      {{ color: #6B7280; font-size: 15px; line-height: 1.7; margin: 0; }}
            .brand {{ margin-top: 32px; font-size: 12px; color: #C8A96A; letter-spacing: 1px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">{icon}</div>
            <h2>{title}</h2>
            <p>{body}</p>
            <div class="brand">SIMPUL • PERENCANA PERNIKAHAN</div>
        </div>
    </body>
    </html>
    """