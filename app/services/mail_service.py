# app/services/mail_service.py
#
# Semua fungsi kirim email dikumpulkan di sini.
# Route tidak boleh langsung memanggil mail.send() — gunakan fungsi di bawah.

from flask_mail import Message
from app.extensions import mail


def send_verification_email(user_name: str, user_email: str, verify_url: str) -> bool:
    """Kirim email verifikasi akun setelah register."""
    try:
        msg = Message(
            subject    = 'Verifikasi Akun Simpul Wedding Planner Anda',
            recipients = [user_email],
        )
        msg.body = (
            f"Halo {user_name},\n\n"
            "Terima kasih telah mendaftar di Simpul Wedding Planner!\n"
            "Klik tautan berikut untuk mengaktifkan akun Anda:\n\n"
            f"{verify_url}\n\n"
            "Jika Anda tidak merasa mendaftar, abaikan email ini.\n\n"
            "Salam hangat,\nTim Simpul"
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"[MailService] Gagal kirim verifikasi ke {user_email}: {e}")
        return False


def send_otp_email(user_name: str, user_email: str, otp_code: str) -> bool:
    """Kirim OTP untuk reset password atau verifikasi perubahan email."""
    try:
        msg = Message(
            subject    = '[Simpul] Kode OTP Anda',
            recipients = [user_email],
        )
        msg.body = (
            f"Halo {user_name},\n\n"
            "Berikut kode OTP verifikasi Anda:\n\n"
            f"  {otp_code}  \n\n"
            "Kode ini berlaku selama 5 menit dan bersifat rahasia.\n"
            "Jangan bagikan kepada siapa pun.\n\n"
            "Salam hangat,\nTim Simpul"
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"[MailService] Gagal kirim OTP ke {user_email}: {e}")
        return False


def send_wedding_date_update_email(
    partner_name: str,
    partner_email: str,
    changer_name: str,
    new_date_display: str,
) -> bool:
    """Notifikasi via email ke pasangan saat tanggal nikah diubah."""
    try:
        msg = Message(
            subject    = '[Simpul] Tanggal Pernikahan Diperbarui 📅',
            recipients = [partner_email],
        )
        msg.body = (
            f"Halo {partner_name},\n\n"
            f"{changer_name} baru saja mengubah tanggal pernikahan "
            f"menjadi {new_date_display}.\n\n"
            "Buka aplikasi Simpul untuk melihat pembaruan hitung mundur.\n\n"
            "Salam hangat,\nTim Simpul"
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"[MailService] Gagal kirim notif tanggal ke {partner_email}: {e}")
        return False