from mi_app import db
from datetime import date
# MODELOS DE LA BASE DE DATOS CREAMOS AQUÍ LAS TABLAS QUE VAMOS A UTILIZAR EN LA APLICACIÓN
# CADA CLASE REPRESENTA UNA TABLA DIFERENTE
class Producto(db.Model):
    __tablename__ = 'producto'
    #LOS ATRIBUTOS DE LA CLASE SON LAS COLUMNAS DE LA TABLA 
    #LOS DATOS LOS METES DE ESTA MANERA LO UNICO RARO ES LAS CLAVES FORANEAS HAY EXPLICACION ABAJO
    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255))
    descripcion = db.Column(db.String(600))
    precio = db.Column(db.Float)
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    #TODAS LAS CLASES TIENE SU CONSTRUCTOR QUE INICIALIZA LOS ATRIBUTOS DE LA CLASE
    def __init__(self, nombre, descripcion, precio, fecha_inicio, fecha_fin):
        self.nombre = nombre
        self.descripcion = descripcion
        self.precio = precio
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin

    def __repr__(self):
        return f'<Producto {self.id_producto}>'


class Usuarios(db.Model):
    __tablename__ = 'usuarios'

    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    contrasena = db.Column(db.String(100))
    fecha_registro = db.Column(db.Date, default=date.today)

    def __init__(self, nombre_usuario, email, contrasena, fecha_registro=None):
        self.nombre_usuario = nombre_usuario
        self.email = email
        self.contrasena = contrasena
        self.fecha_registro = fecha_registro or date.today()

    def __repr__(self):
        return f'<Usuario {self.id_usuario}>'


class Ventas(db.Model):
    __tablename__ = 'ventas'

    id_venta = db.Column(db.Integer, primary_key=True)
    #ESTE ES UN EJEMPLO DE CLAVE FORANEA PARA RELACIONAR TABLAS
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
    id_venta = db.Column(db.Integer, db.ForeignKey('ventas.id_venta'))
    metodo_pago = db.Column(db.String(50))
    cantidad = db.Column(db.Float)
    fecha_pago = db.Column(db.Date, default=date.today)

    venta = db.relationship('Ventas', backref=db.backref('pagos', lazy=True))

    def __init__(self, id_venta, metodo_pago, cantidad, fecha_pago=None):
        self.id_venta = id_venta
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
