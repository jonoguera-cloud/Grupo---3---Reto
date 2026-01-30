from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_jwt_extended import JWTManager



db = SQLAlchemy()
login_manager = LoginManager()
jwt = JWTManager()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://grupo3RETO:admin@localhost/RETO2'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'catalog.login'
app.config['JWT_SECRET_KEY'] = 'donoswawe_567'
app.config['JWT_TOKEN_LOCATION'] = 'cookies'     # Usar cookies para guardar el token
app.config['JWT_COOKIE_SECURE'] = False           # True si usas HTTPS
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'        # cookies accesibles en todo el sitio
app.config['JWT_COOKIE_CSRF_PROTECT'] = False     # opcional, protección CSRF

jwt.init_app(app)

from mi_app.catalogo.vistas import catalog
app.register_blueprint(catalog)

from mi_app.catalogo.modelos import Usuarios

@login_manager.user_loader
def load_user(user_id):
    return Usuarios.query.get(int(user_id))

with app.app_context():
    db.create_all()
