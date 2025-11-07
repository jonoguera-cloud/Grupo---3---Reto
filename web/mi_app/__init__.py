from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# Utilizamos el app.config para conectarnos a la base de datos que esta en postgresql
# Añadimos los datos de nuestra Base de Datos, el usuario y la contraseña.
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://grupo3RETO:admin@localhost/RETO1'
db = SQLAlchemy(app)
from  mi_app.catalogo.vistas import catalog
app.register_blueprint(catalog)
with app.app_context():
    db.create_all()