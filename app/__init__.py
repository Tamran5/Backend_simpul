from flask import Flask
from app.extensions import db, jwt
from flask_migrate import Migrate
from datetime import timedelta
from flask_cors import CORS
from flask_mail import Mail

mail = Mail()

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['SECRET_KEY'] = 'kunci-super-rahasia-simpul'
    
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

    mail.init_app(app) # <--- 4. HUBUNGKAN KE APP

    db.init_app(app)
    jwt.init_app(app)
    Migrate(app, db)
    


    # Registrasi Blueprint
    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.api_routes import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # print(app.url_map)
    # print("----------------------------")

    return app