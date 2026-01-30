from flask import request, Blueprint, render_template, redirect, url_for, flash, jsonify,make_response
from flask_restful import Api, Resource
from mi_app import db
from flask_login import login_user, logout_user, current_user, login_required
from mi_app.catalogo.modelos import Producto, Usuarios, Ventas, Contacto, Pagos
import stripe
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, set_access_cookies
from ..ia import consultar_ia, transcribe_audio
import tempfile
import os
from werkzeug.utils import secure_filename
from mi_app import jwt
from dotenv import load_dotenv

load_dotenv()

# Configura tu clave secreta de Stripe
stripe.api_key = os.getenv("STRIPE_API_KEY")  # Reemplaza con tu clave real o usa variables de entorno

catalog = Blueprint('catalog', __name__)
api = Api(catalog)

# -------------------- PÁGINAS --------------------

@catalog.route('/')
@catalog.route('/home')
def home():
    productos = Producto.query.all()
    return render_template('index.html', productos=productos)


@catalog.route('/contacto')
def contacto():
    return render_template('contacto.html')


# -------------------- CHAT CON OLLAMA --------------------
@catalog.route('/chat/ollama', methods=['POST'])
def chat_ollama():
    """Recibe JSON {message: str} y devuelve la respuesta de Ollama via consultar_ia"""
    data = request.get_json(silent=True) or {}
    message = data.get('message')

    if not message:
        return jsonify({'error': 'No se proporcionó mensaje'}), 400

    try:
        respuesta = consultar_ia(message)
        return jsonify({'reply': respuesta})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@catalog.route('/chat/ollama/audio', methods=['POST'])
def chat_ollama_audio():
    """Recibe un archivo de audio (campo 'audio') -> lo transcribe en el servidor y devuelve la respuesta de Ollama."""
    if 'audio' not in request.files:
        return jsonify({'error': 'No se proporcionó archivo de audio (campo "audio")'}), 400

    f = request.files['audio']
    if f.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    filename = secure_filename(f.filename)
    suffix = os.path.splitext(filename)[1] or '.wav'
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_name = tmp.name
    tmp.close()
    try:
        f.save(tmp_name)
        # Transcribir
        transcript = transcribe_audio(tmp_name)
        # Pasar la transcripción a la IA
        respuesta = consultar_ia(transcript)
        return jsonify({'transcript': transcript, 'reply': respuesta})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        try:
            os.unlink(tmp_name)
        except Exception:
            pass


# -------------------- LOGIN / REGISTRO --------------------

@catalog.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('catalog.home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Usuarios.query.filter_by(nombre_usuario=username).first()
        if user and user.contrasena == password:
            login_user(user, remember=True)
            token = create_access_token(identity=str(user.id_usuario))
            print(f"Token JWT generado para el usuario {token}")
            resp = make_response(redirect(url_for('catalog.index')))
            # Usa la utilidad de flask_jwt_extended para setear la cookie correctamente
            set_access_cookies(resp, token)
            return resp
        flash('Usuario o contraseña incorrectos', 'error')

    return render_template('login.html')


@catalog.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('catalog.home'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if Usuarios.query.filter_by(nombre_usuario=username).first():
            flash('El nombre de usuario ya existe', 'error')
            return render_template('register.html')
        if Usuarios.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'error')
            return render_template('register.html')

        nuevo_usuario = Usuarios(username, email, password)
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('Registro exitoso, ya puedes iniciar sesión', 'success')
        return redirect(url_for('catalog.login'))

    return render_template('register.html')


@catalog.route('/logout')
@login_required
def logout():
    logout_user()
    resp = make_response(redirect(url_for('catalog.home')))
    resp.set_cookie('token', '', expires=0)
    return resp


# -------------------- CONTACTO --------------------

@catalog.route('/api/contacto', methods=['POST'])
def registrar_contacto():
    nombre = request.form.get('nombre')
    correo = request.form.get('email')
    mensaje = request.form.get('mensaje')

    if not nombre or not correo or not mensaje:
        flash('Todos los campos son obligatorios', 'error')
        return redirect(url_for('catalog.contacto'))

    nuevo_contacto = Contacto(nombre=nombre, correo=correo, mensaje=mensaje)
    db.session.add(nuevo_contacto)
    db.session.commit()

    flash('Mensaje enviado correctamente', 'success')
    return redirect(url_for('catalog.contacto'))


# -------------------- COMPRA / VENTAS / PAGOS --------------------

@catalog.route('/comprar/<int:id_producto>', methods=['POST'])
@login_required
def comprar(id_producto):
    cantidad = int(request.form.get('cantidad', 1))
    producto = Producto.query.get_or_404(id_producto)

    if producto.stock < cantidad:
        flash('No hay stock suficiente', 'error')
        return redirect(url_for('catalog.home'))

    total_cents = int(producto.precio * 100) * cantidad  # Stripe requiere céntimos

    # Crear sesión de Stripe
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'eur',
                'product_data': {'name': producto.nombre},
                'unit_amount': total_cents,
            },
            'quantity': cantidad,
        }],
        mode='payment',
        success_url=url_for('catalog.pago_confirmado', id_producto=producto.id_producto, cantidad=cantidad, _external=True),
        cancel_url=url_for('catalog.home', _external=True),
    )

    return redirect(session.url)


@catalog.route('/pago_confirmado/<int:id_producto>/<int:cantidad>')
@login_required
def pago_confirmado(id_producto, cantidad):
    producto = Producto.query.get_or_404(id_producto)

    # Calcular total
    total = producto.precio * cantidad

    # Guardar venta
    nueva_venta = Ventas(
        id_producto=producto.id_producto,
        id_usuario=current_user.id_usuario,
        cantidad=cantidad,
        total=total
    )
    db.session.add(nueva_venta)
    db.session.commit()

    # Guardar pago
    nuevo_pago = Pagos(
        id_venta=nueva_venta.id_venta,
        id_usuario=current_user.id_usuario,
        metodo_pago='stripe',
        cantidad=total
    )
    db.session.add(nuevo_pago)

    # Actualizar stock
    producto.stock -= cantidad
    db.session.commit()

    flash('Compra realizada correctamente', 'success')
    return redirect(url_for('catalog.home'))


# -------------------- REST API ENDPOINTS --------------------

# Recurso para Productos
class ProductoResource(Resource):
    """Endpoints para gestionar Productos"""
    @jwt_required(locations=["cookies"])
    def get(self, id_producto=None):
        """GET: Obtener producto(s)"""
        if id_producto:
            producto = Producto.query.get(id_producto)
            if not producto:
                return {'mensaje': 'Producto no encontrado'}, 404
            return {
                'id_producto': producto.id_producto,
                'nombre': producto.nombre,
                'descripcion': producto.descripcion,
                'precio': producto.precio,
                'fecha_inicio': str(producto.fecha_inicio),
                'fecha_fin': str(producto.fecha_fin),
                'stock': producto.stock
            }
        else:
            productos = Producto.query.all()
            return {
                'total': len(productos),
                'productos': [{
                    'id_producto': p.id_producto,
                    'nombre': p.nombre,
                    'descripcion': p.descripcion,
                    'precio': p.precio,
                    'fecha_inicio': str(p.fecha_inicio),
                    'fecha_fin': str(p.fecha_fin),
                    'stock': p.stock
                } for p in productos]
            }
    
    def post(self):
        """POST: Crear nuevo Producto"""
        datos = request.get_json()
        
        if not all(k in datos for k in ['nombre', 'descripcion', 'precio', 'fecha_inicio', 'fecha_fin']):
            return {'mensaje': 'Faltan campos requeridos'}, 400
        
        try:
            nuevo_producto = Producto(
                nombre=datos['nombre'],
                descripcion=datos['descripcion'],
                precio=datos['precio'],
                fecha_inicio=datos['fecha_inicio'],
                fecha_fin=datos['fecha_fin'],
                stock=datos.get('stock', 100)
            )
            db.session.add(nuevo_producto)
            db.session.commit()
            
            return {
                'mensaje': 'Producto creado exitosamente',
                'id_producto': nuevo_producto.id_producto
            }, 201
        except Exception as e:
            db.session.rollback()
            return {'mensaje': f'Error: {str(e)}'}, 500
    
    def put(self, id_producto):
        """PUT: Actualizar Producto"""
        producto = Producto.query.get(id_producto)
        if not producto:
            return {'mensaje': 'Producto no encontrado'}, 404
        
        datos = request.get_json()
        
        try:
            if 'nombre' in datos:
                producto.nombre = datos['nombre']
            if 'descripcion' in datos:
                producto.descripcion = datos['descripcion']
            if 'precio' in datos:
                producto.precio = datos['precio']
            if 'fecha_inicio' in datos:
                producto.fecha_inicio = datos['fecha_inicio']
            if 'fecha_fin' in datos:
                producto.fecha_fin = datos['fecha_fin']
            if 'stock' in datos:
                producto.stock = datos['stock']
            
            db.session.commit()
            return {'mensaje': 'Producto actualizado exitosamente'}
        except Exception as e:
            db.session.rollback()
            return {'mensaje': f'Error: {str(e)}'}, 500
    
    def delete(self, id_producto):
        """DELETE: Eliminar Producto"""
        producto = Producto.query.get(id_producto)
        if not producto:
            return {'mensaje': 'Producto no encontrado'}, 404
        
        try:
            db.session.delete(producto)
            db.session.commit()
            return {'mensaje': 'Producto eliminado exitosamente'}
        except Exception as e:
            db.session.rollback()
            return {'mensaje': f'Error: {str(e)}'}, 500


# Recurso para Usuarios
class UsuarioResource(Resource):
    """Endpoints para gestionar Usuarios"""
    @jwt_required(locations=["cookies"])
    def get(self, id_usuario=None):
        """GET: Obtener usuario(s)"""
        if id_usuario:
            usuario = Usuarios.query.get(id_usuario)
            if not usuario:
                return {'mensaje': 'Usuario no encontrado'}, 404
            return {
                'id_usuario': usuario.id_usuario,
                'nombre_usuario': usuario.nombre_usuario,
                'email': usuario.email,
                'fecha_registro': str(usuario.fecha_registro)
            }
        else:
            usuarios = Usuarios.query.all()
            return {
                'total': len(usuarios),
                'usuarios': [{
                    'id_usuario': u.id_usuario,
                    'nombre_usuario': u.nombre_usuario,
                    'email': u.email,
                    'fecha_registro': str(u.fecha_registro)
                } for u in usuarios]
            }
    
    def post(self):
        """POST: Crear nuevo Usuario"""
        datos = request.get_json()
        
        if not all(k in datos for k in ['nombre_usuario', 'email', 'contrasena']):
            return {'mensaje': 'Faltan campos requeridos'}, 400
        
        if Usuarios.query.filter_by(nombre_usuario=datos['nombre_usuario']).first():
            return {'mensaje': 'El nombre de usuario ya existe'}, 400
        
        if Usuarios.query.filter_by(email=datos['email']).first():
            return {'mensaje': 'El email ya está registrado'}, 400
        
        try:
            nuevo_usuario = Usuarios(
                nombre_usuario=datos['nombre_usuario'],
                email=datos['email'],
                contrasena=datos['contrasena']
            )
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            return {
                'mensaje': 'Usuario creado exitosamente',
                'id_usuario': nuevo_usuario.id_usuario
            }, 201
        except Exception as e:
            db.session.rollback()
            return {'mensaje': f'Error: {str(e)}'}, 500
    
    def put(self, id_usuario):
        """PUT: Actualizar Usuario"""
        usuario = Usuarios.query.get(id_usuario)
        if not usuario:
            return {'mensaje': 'Usuario no encontrado'}, 404
        
        datos = request.get_json()
        
        try:
            if 'email' in datos:
                if Usuarios.query.filter_by(email=datos['email']).first():
                    return {'mensaje': 'El email ya está en uso'}, 400
                usuario.email = datos['email']
            if 'contrasena' in datos:
                usuario.contrasena = datos['contrasena']
            
            db.session.commit()
            return {'mensaje': 'Usuario actualizado exitosamente'}
        except Exception as e:
            db.session.rollback()
            return {'mensaje': f'Error: {str(e)}'}, 500
    
    def delete(self, id_usuario):
        """DELETE: Eliminar Usuario"""
        usuario = Usuarios.query.get(id_usuario)
        if not usuario:
            return {'mensaje': 'Usuario no encontrado'}, 404
        
        try:
            db.session.delete(usuario)
            db.session.commit()
            return {'mensaje': 'Usuario eliminado exitosamente'}
        except Exception as e:
            db.session.rollback()
            return {'mensaje': f'Error: {str(e)}'}, 500


# Recurso para Ventas
class VentaResource(Resource):
    """Endpoints para gestionar Ventas"""
    @jwt_required(locations=["cookies"])
    def get(self, id_venta=None):
        """GET: Obtener venta(s)"""
        if id_venta:
            venta = Ventas.query.get(id_venta)
            if not venta:
                return {'mensaje': 'Venta no encontrada'}, 404
            return {
                'id_venta': venta.id_venta,
                'id_producto': venta.id_producto,
                'id_usuario': venta.id_usuario,
                'cantidad': venta.cantidad,
                'total': venta.total,
                'fecha_venta': str(venta.fecha_venta)
            }
        else:
            ventas = Ventas.query.all()
            return {
                'total': len(ventas),
                'ventas': [{
                    'id_venta': v.id_venta,
                    'id_producto': v.id_producto,
                    'id_usuario': v.id_usuario,
                    'cantidad': v.cantidad,
                    'total': v.total,
                    'fecha_venta': str(v.fecha_venta)
                } for v in ventas]
            }
    
    def post(self):
        """POST: Crear nueva Venta"""
        datos = request.get_json()
        
        if not all(k in datos for k in ['id_producto', 'id_usuario', 'cantidad', 'total']):
            return {'mensaje': 'Faltan campos requeridos'}, 400
        
        try:
            nueva_venta = Ventas(
                id_producto=datos['id_producto'],
                id_usuario=datos['id_usuario'],
                cantidad=datos['cantidad'],
                total=datos['total']
            )
            db.session.add(nueva_venta)
            db.session.commit()
            
            return {
                'mensaje': 'Venta creada exitosamente',
                'id_venta': nueva_venta.id_venta
            }, 201
        except Exception as e:
            db.session.rollback()
            return {'mensaje': f'Error: {str(e)}'}, 500
    
    def put(self, id_venta):
        """PUT: Actualizar Venta"""
        venta = Ventas.query.get(id_venta)
        if not venta:
            return {'mensaje': 'Venta no encontrada'}, 404
        
        datos = request.get_json()
        
        try:
            if 'cantidad' in datos:
                venta.cantidad = datos['cantidad']
            if 'total' in datos:
                venta.total = datos['total']
            
            db.session.commit()
            return {'mensaje': 'Venta actualizada exitosamente'}
        except Exception as e:
            db.session.rollback()
            return {'mensaje': f'Error: {str(e)}'}, 500
    
    def delete(self, id_venta):
        """DELETE: Eliminar Venta"""
        venta = Ventas.query.get(id_venta)
        if not venta:
            return {'mensaje': 'Venta no encontrada'}, 404
        
        try:
            db.session.delete(venta)
            db.session.commit()
            return {'mensaje': 'Venta eliminada exitosamente'}
        except Exception as e:
            db.session.rollback()
            return {'mensaje': f'Error: {str(e)}'}, 500


# Recurso para Pagos
class PagoResource(Resource):
    """Endpoints para gestionar Pagos"""
    @jwt_required(locations=["cookies"])
    def get(self, id_pago=None):
        """GET: Obtener pago(s)"""
        if id_pago:
            pago = Pagos.query.get(id_pago)
            if not pago:
                return {'mensaje': 'Pago no encontrado'}, 404
            return {
                'id_pago': pago.id_pago,
                'id_venta': pago.id_venta,
                'id_usuario': pago.id_usuario,
                'metodo_pago': pago.metodo_pago,
                'cantidad': pago.cantidad,
                'fecha_pago': str(pago.fecha_pago)
            }
        else:
            pagos = Pagos.query.all()
            return {
                'total': len(pagos),
                'pagos': [{
                    'id_pago': p.id_pago,
                    'id_venta': p.id_venta,
                    'id_usuario': p.id_usuario,
                    'metodo_pago': p.metodo_pago,
                    'cantidad': p.cantidad,
                    'fecha_pago': str(p.fecha_pago)
                } for p in pagos]
            }
    
    def post(self):
        """POST: Crear nuevo Pago"""
        datos = request.get_json()
        
        if not all(k in datos for k in ['id_venta', 'id_usuario', 'metodo_pago', 'cantidad']):
            return {'mensaje': 'Faltan campos requeridos'}, 400
        
        try:
            nuevo_pago = Pagos(
                id_venta=datos['id_venta'],
                id_usuario=datos['id_usuario'],
                metodo_pago=datos['metodo_pago'],
                cantidad=datos['cantidad']
            )
            db.session.add(nuevo_pago)
            db.session.commit()
            
            return {
                'mensaje': 'Pago creado exitosamente',
                'id_pago': nuevo_pago.id_pago
            }, 201
        except Exception as e:
            db.session.rollback()
            return {'mensaje': f'Error: {str(e)}'}, 500
    
    def put(self, id_pago):
        """PUT: Actualizar Pago"""
        pago = Pagos.query.get(id_pago)
        if not pago:
            return {'mensaje': 'Pago no encontrado'}, 404
        
        datos = request.get_json()
        
        try:
            if 'metodo_pago' in datos:
                pago.metodo_pago = datos['metodo_pago']
            if 'cantidad' in datos:
                pago.cantidad = datos['cantidad']
            
            db.session.commit()
            return {'mensaje': 'Pago actualizado exitosamente'}
        except Exception as e:
            db.session.rollback()
            return {'mensaje': f'Error: {str(e)}'}, 500
    
    def delete(self, id_pago):
        """DELETE: Eliminar Pago"""
        pago = Pagos.query.get(id_pago)
        if not pago:
            return {'mensaje': 'Pago no encontrado'}, 404
        
        try:
            db.session.delete(pago)
            db.session.commit()
            return {'mensaje': 'Pago eliminado exitosamente'}
        except Exception as e:
            db.session.rollback()
            return {'mensaje': f'Error: {str(e)}'}, 500


# Registrar recursos REST
api.add_resource(ProductoResource, '/api/productos', '/api/productos/<int:id_producto>')
api.add_resource(UsuarioResource, '/api/usuarios', '/api/usuarios/<int:id_usuario>')
api.add_resource(VentaResource, '/api/ventas', '/api/ventas/<int:id_venta>')
api.add_resource(PagoResource, '/api/pagos', '/api/pagos/<int:id_pago>')


@catalog.route("/ia", methods=["POST"])
def ia():
    prompt = request.json["prompt"]
    respuesta = consultar_ia(prompt)
    return jsonify({"respuesta": respuesta})

@catalog.route('/')
def index():
    return render_template('index.html')

# Endpoint para recibir texto de voz
@catalog.route('/procesar_voz', methods=['POST'])
def procesar_voz():
    data = request.json
    texto = data.get('texto')

    # Aquí llamas a tu módulo de IA
    respuesta_ia = f"IA responde a: {texto}"  # Ejemplo simple

    return jsonify({"respuesta": respuesta_ia})

