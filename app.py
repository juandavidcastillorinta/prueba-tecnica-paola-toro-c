from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os
from dotenv import load_dotenv
import xmlrpc.client

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
motor_db = create_engine(os.getenv('DATABASE_URL'))
Base = declarative_base()
Sesion = sessionmaker(bind=motor_db)

class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    correo_electronico = Column(String(255), unique=True, nullable=False)
    contrasena = Column(String(255), nullable=False)
    tareas = relationship('Tarea', backref='usuario', lazy=True)

class Tarea(Base):
    __tablename__ = 'tareas'
    id = Column(Integer, primary_key=True)
    titulo = Column(String(100), nullable=False)
    descripcion = Column(Text)
    fecha_vencimiento = Column(Date)
    estado = Column(String(20), nullable=False)
    id_usuario = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    id_personaje = Column(Integer)

Base.metadata.create_all(motor_db)

def obtener_sesion_db():
    return Sesion()

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        correo = request.form['correo']
        contra = generate_password_hash(request.form['contra'])
        if not correo or not request.form['contra']:
            flash('Campos obligatorios')
            return redirect(url_for('registro'))
        sesion_db = obtener_sesion_db()
        nuevo_usuario = Usuario(correo_electronico=correo, contrasena=contra)
        sesion_db.add(nuevo_usuario)
        sesion_db.commit()
        sesion_db.close()
        flash('Registro exitoso')
        return redirect(url_for('login'))
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contra = request.form['contra']
        sesion_db = obtener_sesion_db()
        usuario = sesion_db.query(Usuario).filter_by(correo_electronico=correo).first()
        sesion_db.close()
        if usuario and check_password_hash(usuario.contrasena, contra):
            session['id_usuario'] = usuario.id
            return redirect(url_for('listado_tareas'))
        flash('Credenciales inválidas')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('id_usuario', None)
    return redirect(url_for('login'))

@app.route('/tareas', methods=['GET'])
def listado_tareas():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    sesion_db = obtener_sesion_db()
    tareas_usuario = sesion_db.query(Tarea).filter_by(id_usuario=session['id_usuario']).all()
    sesion_db.close()
    # Obtengo info de personajes si asociados
    tareas_con_personajes = []
    for tarea in tareas_usuario:
        if tarea.id_personaje:
            resp_api = requests.get(f"https://rickandmortyapi.com/api/character/{tarea.id_personaje}")
            if resp_api.status_code == 200:
                data = resp_api.json()
                personaje = {'nombre': data['name'], 'imagen': data['image']}
            else:
                personaje = None
        else:
            personaje = None
        tareas_con_personajes.append({'tarea': tarea, 'personaje': personaje})
    return render_template('tareas.html', tareas=tareas_con_personajes)

@app.route('/crear_tarea', methods=['GET', 'POST'])
def crear_tarea():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        fecha_venc = request.form['fecha_vencimiento']
        estado = request.form['estado']
        if not titulo or not estado:
            flash('Título y estado obligatorios')
            return redirect(url_for('crear_tarea'))
        sesion_db = obtener_sesion_db()
        nueva_tarea = Tarea(titulo=titulo, descripcion=descripcion, fecha_vencimiento=fecha_venc, estado=estado, id_usuario=session['id_usuario'])
        sesion_db.add(nueva_tarea)
        sesion_db.commit()
        sesion_db.close()
        return redirect(url_for('listado_tareas'))
    return render_template('crear_tarea.html')

@app.route('/editar_tarea/<int:id_tarea>', methods=['GET', 'POST'])
def editar_tarea(id_tarea):
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    sesion_db = obtener_sesion_db()
    tarea = sesion_db.query(Tarea).filter_by(id=id_tarea, id_usuario=session['id_usuario']).first()
    if not tarea:
        flash('Tarea no encontrada')
        return redirect(url_for('listado_tareas'))
    if request.method == 'POST':
        tarea.titulo = request.form['titulo']
        tarea.descripcion = request.form['descripcion']
        tarea.fecha_vencimiento = request.form['fecha_vencimiento']
        tarea.estado = request.form['estado']
        sesion_db.commit()
        sesion_db.close()
        return redirect(url_for('listado_tareas'))
    sesion_db.close()
    return render_template('editar_tarea.html', tarea=tarea)

@app.route('/eliminar_tarea/<int:id_tarea>')
def eliminar_tarea(id_tarea):
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    sesion_db = obtener_sesion_db()
    tarea = sesion_db.query(Tarea).filter_by(id=id_tarea, id_usuario=session['id_usuario']).first()
    if tarea:
        sesion_db.delete(tarea)
        sesion_db.commit()
    sesion_db.close()
    return redirect(url_for('listado_tareas'))

@app.route('/personajes', methods=['GET'])
def listar_personajes():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    resp_api = requests.get("https://rickandmortyapi.com/api/character")
    if resp_api.status_code == 200:
        personajes = resp_api.json()['results']
        return render_template('personajes.html', personajes=personajes)
    flash('Error al cargar API')
    return redirect(url_for('listado_tareas'))

@app.route('/asociar_personaje/<int:id_tarea>/<int:id_personaje>')
def asociar_personaje(id_tarea, id_personaje):
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    sesion_db = obtener_sesion_db()
    tarea = sesion_db.query(Tarea).filter_by(id=id_tarea, id_usuario=session['id_usuario']).first()
    if tarea:
        tarea.id_personaje = id_personaje
        sesion_db.commit()
    sesion_db.close()
    return redirect(url_for('listado_tareas'))

@app.route('/enviar_a_odoo/<int:id_tarea>')
def enviar_a_odoo(id_tarea):
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    sesion_db = obtener_sesion_db()
    tarea = sesion_db.query(Tarea).filter_by(id=id_tarea, id_usuario=session['id_usuario']).first()
    sesion_db.close()
    if not tarea:
        flash('Tarea no encontrada')
        return redirect(url_for('listado_tareas'))
    url_odoo = os.getenv('ODOO_URL')
    db_odoo = os.getenv('ODOO_DB')
    usuario_odoo = os.getenv('ODOO_USER')
    contra_odoo = os.getenv('ODOO_PASSWORD')
    
    try:
        common = xmlrpc.client.ServerProxy(f'{url_odoo}/xmlrpc/2/common')
        uid = common.authenticate(db_odoo, usuario_odoo, contra_odoo, {})
        
        models = xmlrpc.client.ServerProxy(f'{url_odoo}/xmlrpc/2/object')
        nuevo_id = models.execute_kw(db_odoo, uid, contra_odoo, 'tareas.rickmorty', 'create', [{
            'titulo': tarea.titulo,
            'descripcion': tarea.descripcion,
            'fecha_vencimiento': str(tarea.fecha_vencimiento) if tarea.fecha_vencimiento else False,
            'estado': tarea.estado,
            'id_personaje': tarea.id_personaje or 0,
        }])
        flash('Tarea enviada a Odoo exitosamente')
    except Exception as e:
        flash(f'Error al enviar a Odoo: {str(e)}')
    return redirect(url_for('listado_tareas'))

@app.route('/')
def index():
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)