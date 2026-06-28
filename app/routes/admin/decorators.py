# app/routes/admin/decorators.py
#
# Decorator khusus admin web (session-based).
# Berbeda dari @jwt_required() yang dipakai oleh Flutter mobile.

import functools
from flask import session, redirect, url_for


def login_required(view):
    """Proteksi halaman admin — redirect ke login jika session kosong."""
    @functools.wraps(view)
    def wrapped(**kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('auth_web.login'))
        return view(**kwargs)
    return wrapped