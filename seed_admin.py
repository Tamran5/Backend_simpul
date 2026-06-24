from app import create_app
from app.extensions import db
from app.models import Admin

app = create_app()

def seed_admin_account():
    with app.app_context():
        email_target = "admin@simpul.com"
        admin_exists = Admin.query.filter_by(email=email_target).first()
        
        if not admin_exists:
            admin = Admin()
            admin.name = "Super Admin Simpul"
            admin.email = email_target
            admin.set_password("rahasia123") 
            
            db.session.add(admin)
            db.session.commit()
            print("\n[SUKSES] Akun admin pertama berhasil ditanam ke MySQL!")
            print(f"Email   : {email_target}\nPassword: admin123\n")
        else:
            print("\n[INFO] Akun admin sudah terdaftar di MySQL.\n")

if __name__ == '__main__':
    seed_admin_account()