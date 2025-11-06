from flask  import request, jsonify, Blueprint, render_template
from mi_app import db
from mi_app.catalogo.modelos import Producto, Usuarios, Ventas, Contacto, Pagos

catalog = Blueprint('catalog',__name__)

@catalog.route('/')

@catalog.route('/home')
def home():
    return render_template('index.html')

@catalog.route('/productos')
def productos():
    return render_template('productos.html')

@catalog.route('/contacto')
def contacto():
    return render_template('contacto.html')

# -------------------- PRODUCTOS (Entradas) --------------------
@catalog.route('/api/productos', methods=['GET'])
def listar_productos():
    productos = Producto.query.all()
    res = [{
        'id_producto': p.id_producto,
        'nombre': p.nombre,
        'descripcion': p.descripcion,
        'precio': p.precio,
        'fecha_inicio': str(p.fecha_inicio),
        'fecha_fin': str(p.fecha_fin)
    } for p in productos]
    return jsonify(res)


@catalog.route('/producto/<int:id>', methods=['GET'])
def obtener_producto(id):
    producto = Producto.query.get_or_404(id)
    return jsonify({
        'id_producto': producto.id_producto,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'precio': producto.precio,
        'fecha_inicio': str(producto.fecha_inicio),
        'fecha_fin': str(producto.fecha_fin)
    })


@catalog.route('/producto', methods=['POST'])
def crear_producto():
    data = request.get_json()
    nuevo = Producto(
        nombre=data.get('nombre'),
        descripcion=data.get('descripcion'),
        precio=data.get('precio'),
        fecha_inicio=data.get('fecha_inicio'),
        fecha_fin=data.get('fecha_fin')
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({'mensaje': 'Producto creado correctamente'}), 201


# -------------------- USUARIOS --------------------
@catalog.route('/usuarios', methods=['GET'])
def listar_usuarios():
    usuarios = Usuarios.query.all()
    res = [{
        'id_usuario': u.id_usuario,
        'nombre_usuario': u.nombre_usuario,
        'email': u.email,
        'fecha_registro': str(u.fecha_registro)
    } for u in usuarios]
    return jsonify(res)


@catalog.route('/usuario/<int:id>', methods=['GET'])
def obtener_usuario(id):
    usuario = Usuarios.query.get_or_404(id)
    return jsonify({
        'id_usuario': usuario.id_usuario,
        'nombre_usuario': usuario.nombre_usuario,
        'email': usuario.email,
        'fecha_registro': str(usuario.fecha_registro)
    })


@catalog.route('/api/contacto', methods=['POST'])
def registrar_contacto():
    """
    Ruta para registrar mensajes del formulario de contacto (desde el HTML).
    """
    nombre = request.form.get('nombre')
    correo = request.form.get('email')
    mensaje = request.form.get('mensaje')

    if not nombre or not correo or not mensaje:
        return jsonify({'error': 'Todos los campos son obligatorios'}), 400

    nuevo_contacto = Contacto(nombre=nombre, correo=correo, mensaje=mensaje)

    db.session.add(nuevo_contacto)
    db.session.commit()

    return render_template('contacto.html', enviado=True)

@catalog.route('/api/contactos', methods=['GET'])
def listar_contactos():
    """
    Devuelve todos los contactos registrados en formato JSON.
    """
    contactos = Contacto.query.order_by(Contacto.fecha_envio.desc()).all()

    resultado = [{
        'id_contacto': c.id_contacto,
        'nombre': c.nombre,
        'correo': c.correo,
        'mensaje': c.mensaje,
        'fecha_envio': str(c.fecha_envio)
    } for c in contactos]

    return jsonify(resultado)

# -------------------- VENTAS --------------------
@catalog.route('/ventas', methods=['GET'])
def listar_ventas():
    ventas = Ventas.query.all()
    res = [{
        'id_venta': v.id_venta,
        'id_entrada': v.id_entrada,
        'total': v.total,
        'fecha_venta': str(v.fecha_venta)
    } for v in ventas]
    return jsonify(res)


# -------------------- PAGOS --------------------
@catalog.route('/pagos', methods=['GET'])
def listar_pagos():
    pagos = Pagos.query.all()
    res = [{
        'id_pago': p.id_pago,
        'id_venta': p.id_venta,
        'metodo_pago': p.metodo_pago,
        'cantidad': p.cantidad,
        'fecha_pago': str(p.fecha_pago)
    } for p in pagos]
    return jsonify(res)
