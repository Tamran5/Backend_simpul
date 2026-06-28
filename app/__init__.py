from flask import Flask
from app.extensions import db, jwt, migrate
from flask_migrate import Migrate
from datetime import timedelta
from flask_cors import CORS
from flask_mail import Mail

mail = Mail()

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['SECRET_KEY'] = 'kunci-super-rahasia-simpul'

    app.config["UPLOAD_FOLDER"] = "app/static/uploads/profile"
    app.config["ALLOWED_EXTENSIONS"] = {
        "png",
        "jpg",
        "jpeg",
        "gif",
        "webp"
    }
    
    # KONEKSI MYSQL: mysql+pymysql://username:password@host:port/nama_db
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/db_simpul'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['JWT_SECRET_KEY'] = 'super-secret-key-simpul-wedding-planner-2026-caps'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

    # KONFIGURASI SMTP GMAIL 
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'mohtabahmaulana@gmail.com' 
    app.config['MAIL_PASSWORD'] = 'entj oodf jfgb lswj' 
    app.config['MAIL_DEFAULT_SENDER'] = ('Simpul Wedding', 'simpulapp@gmail.com')

   # ── Init extensions ───────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
 
    # ── Daftarkan semua blueprint ─────────────────────────────────────────────
    _register_blueprints(app)
 
    # ── Buat tabel (development only) ─────────────────────────────────────────
    with app.app_context():
        db.create_all()
 
    return app
 
 
def _register_blueprints(app: Flask) -> None:
    from app.routes.auth          import auth_bp
    from app.routes.profile       import profile_bp
    from app.routes.partner       import partner_bp
    from app.routes.home          import home_bp
    from app.routes.articles      import articles_bp
    from app.routes.vendors       import vendors_bp
    from app.routes.notifications import notifications_bp
    from app.routes.main_routes   import main_bp
    from app.routes.journey       import journey_bp


 
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(partner_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(articles_bp)
    app.register_blueprint(vendors_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(journey_bp)
    

    from app.routes.admin import auth_web_bp, pages_bp, api_articles_bp, api_vendors_bp, api_users_bp, admin_bp
 
    app.register_blueprint(auth_web_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(api_articles_bp)
    app.register_blueprint(api_vendors_bp)
    app.register_blueprint(api_users_bp)
    app.register_blueprint(admin_bp)