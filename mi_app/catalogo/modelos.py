from mi_app import db
from datetime import date


class Producto(db.Model):
    __tablename__ = 'producto'

    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255))
    descripcion = db.Column(db.String(600))
    precio = db.Column(db.Float)
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)

    # NUEVO CAMPO: stock disponible
    stock = db.Column(db.Integer, default=100)

    def __init__(self, nombre, descripcion, precio, fecha_inicio, fecha_fin, stock=100):
        self.nombre = nombre
        self.descripcion = descripcion
        self.precio = precio
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.stock = stock

    def __repr__(self):
        return f'<Producto {self.id_producto} - Stock: {self.stock}>'


class Usuarios(db.Model):
    __tablename__ = 'usuarios'

    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    contrasena = db.Column(db.String(100))
    fecha_registro = db.Column(db.Date, default=date.today)

    def __init__(self, nombre_usuario, email, contrasena, fecha_registro=None):
        self.nombre_usuario = nombre_usuario
        self.email = email
        self.contrasena = contrasena
        self.fecha_registro = fecha_registro or date.today()

    # flask-login
    def is_authenticated(self): return True
    def is_active(self): return True
    def is_anonymous(self): return False
    def get_id(self): return str(self.id_usuario)


class Ventas(db.Model):
    __tablename__ = 'ventas'

    id_venta = db.Column(db.Integer, primary_key=True)

    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'))
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))

    cantidad = db.Column(db.Integer)
    total = db.Column(db.Float)
    fecha_venta = db.Column(db.Date, default=date.today)

    producto = db.relationship('Producto', backref=db.backref('ventas', lazy=True))
    usuario = db.relationship('Usuarios', backref=db.backref('ventas', lazy=True))

    def __init__(self, id_producto, id_usuario, cantidad, total, fecha_venta=None):
        self.id_producto = id_producto
        self.id_usuario = id_usuario
        self.cantidad = cantidad
        self.total = total
        self.fecha_venta = fecha_venta or date.today()

    def __repr__(self):
        return f'<Venta {self.id_venta}>'


class Pagos(db.Model):
    __tablename__ = 'pagos'

    id_pago = db.Column(db.Integer, primary_key=True)

    # relación con venta
    id_venta = db.Column(db.Integer, db.ForeignKey('ventas.id_venta'))

    # NUEVO: relación directa con usuario
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))

    metodo_pago = db.Column(db.String(50))
    cantidad = db.Column(db.Float)
    fecha_pago = db.Column(db.Date, default=date.today)

    venta = db.relationship('Ventas', backref=db.backref('pagos', lazy=True))
    usuario = db.relationship('Usuarios', backref=db.backref('pagos', lazy=True))

    def __init__(self, id_venta, id_usuario, metodo_pago, cantidad, fecha_pago=None):
        self.id_venta = id_venta
        self.id_usuario = id_usuario
        self.metodo_pago = metodo_pago
        self.cantidad = cantidad
        self.fecha_pago = fecha_pago or date.today()

    def __repr__(self):
        return f'<Pago {self.id_pago}>'


class Contacto(db.Model):
    __tablename__ = 'contacto'

    id_contacto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    correo = db.Column(db.String(120))
    mensaje = db.Column(db.Text)
    fecha_envio = db.Column(db.Date, default=date.today)

    def __init__(self, nombre, correo, mensaje, fecha_envio=None):
        self.nombre = nombre
        self.correo = correo
        self.mensaje = mensaje
        self.fecha_envio = fecha_envio or date.today()

    def __repr__(self):
        return f'<Contacto {self.id_contacto}>'
