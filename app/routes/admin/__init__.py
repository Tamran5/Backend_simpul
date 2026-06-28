from .auth_web     import auth_web_bp
from .pages        import pages_bp
from .api_articles import api_articles_bp
from .api_vendors  import api_vendors_bp
from .api_users    import api_users_bp
from .admin        import admin_bp

__all__ = ['auth_web_bp', 'pages_bp', 'api_articles_bp', 'api_vendors_bp', 'api_users_bp', 'admin_bp']