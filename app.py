from datetime import datetime, timedelta
from email.message import EmailMessage
from functools import wraps
from io import BytesIO, StringIO
import csv
import json
import math
import os
import re
import smtplib
import time
import unicodedata

from flask import (
    Flask,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    stream_with_context,
    url_for,
)
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, or_, text
from sqlalchemy.exc import IntegrityError, OperationalError
from werkzeug.security import check_password_hash, generate_password_hash


APP_NAME = "NexoTP"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "nexotp-dev")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///nexotp.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SMTP_HOST"] = os.environ.get("SMTP_HOST", "")
app.config["SMTP_PORT"] = int(os.environ.get("SMTP_PORT", "587"))
app.config["SMTP_USER"] = os.environ.get("SMTP_USER", "")
app.config["SMTP_PASSWORD"] = os.environ.get("SMTP_PASSWORD", "")
app.config["MAIL_FROM"] = os.environ.get("MAIL_FROM", "noreply@nexotp.local")

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Ingresa para continuar."
login_manager.login_message_category = "info"


class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    especialidad = db.Column(db.String(100), nullable=False)
    liceo = db.Column(db.String(180), default="Liceo Comercial Vate Vicente Huidobro")
    comuna = db.Column(db.String(100), nullable=False)
    pais = db.Column(db.String(100), default="Chile")
    telefono = db.Column(db.String(40))
    foto_url = db.Column(db.String(255))
    fecha_nacimiento = db.Column(db.String(20))
    disponibilidad = db.Column(db.String(60), default="Flexible")
    modalidad_preferida = db.Column(db.String(60), default="Hibrida")
    sobre_mi = db.Column(db.Text)
    perfil_profesional = db.Column(db.Text)
    experiencia_resumen = db.Column(db.Text)
    objetivo_profesional = db.Column(db.Text)
    habilidades = db.Column(db.Text)
    habilidades_tecnicas = db.Column(db.Text)
    habilidades_blandas = db.Column(db.Text)
    idiomas = db.Column(db.Text)
    herramientas = db.Column(db.Text)
    certificaciones = db.Column(db.Text)
    carrera_titulo = db.Column(db.String(180))
    institucion = db.Column(db.String(180))
    anio_ingreso = db.Column(db.String(10))
    anio_egreso = db.Column(db.String(10))
    cursos_relevantes = db.Column(db.Text)
    experiencia_laboral = db.Column(db.Text)
    proyectos = db.Column(db.Text)
    referencias = db.Column(db.Text)
    portafolio = db.Column(db.String(255))
    linkedin = db.Column(db.String(255))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    postulaciones = db.relationship(
        "Postulacion", backref="usuario", cascade="all, delete-orphan", lazy=True
    )

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    @property
    def iniciales(self):
        return f"{self.nombre[:1]}{self.apellido[:1]}".upper()

    @property
    def habilidades_lista(self):
        return [h.strip() for h in (self.habilidades or "").split(",") if h.strip()]

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Empresa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    rubro = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    ubicacion = db.Column(db.String(150), nullable=False)
    contacto = db.Column(db.String(120))
    web = db.Column(db.String(255))
    foto_url = db.Column(db.String(255))
    logo_inicial = db.Column(db.String(5))
    color = db.Column(db.String(20), default="#1f2937")
    amigable_tp = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    ofertas = db.relationship(
        "Oferta", backref="empresa", cascade="all, delete-orphan", lazy=True
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Oferta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey("empresa.id"), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    especialidad_req = db.Column(db.String(100), nullable=False)
    comuna = db.Column(db.String(100), nullable=False)
    modalidad = db.Column(db.String(60), nullable=False)
    jornada = db.Column(db.String(60), nullable=False)
    tipo = db.Column(db.String(40), default="Empleo")
    sueldo = db.Column(db.String(80))
    vacantes = db.Column(db.Integer, default=1)
    requiere_experiencia = db.Column(db.Boolean, default=False)
    incluye_mentoria = db.Column(db.Boolean, default=True)
    mentor_nombre = db.Column(db.String(120))
    mentor_cargo = db.Column(db.String(120))
    mentor_email = db.Column(db.String(150))
    mentor_bio = db.Column(db.Text)
    fecha_inicio = db.Column(db.String(20))
    fecha_fin = db.Column(db.String(20))
    convenio_digital = db.Column(db.Text)
    horas_practica = db.Column(db.Integer, default=450)
    requisitos = db.Column(db.Text)
    fecha_publicacion = db.Column(db.DateTime, default=datetime.utcnow)
    activa = db.Column(db.Boolean, default=True)

    postulaciones = db.relationship(
        "Postulacion", backref="oferta", cascade="all, delete-orphan", lazy=True
    )

    @property
    def requisitos_lista(self):
        return [r.strip() for r in (self.requisitos or "").split(";") if r.strip()]

    @property
    def es_practica(self):
        return self.tipo == "Practica" or "practica" in (self.jornada or "").lower()


class Postulacion(db.Model):
    __table_args__ = (
        db.UniqueConstraint("usuario_id", "oferta_id", name="unique_postulacion"),
    )
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    oferta_id = db.Column(db.Integer, db.ForeignKey("oferta.id"), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(50), default="En revision")
    mensaje = db.Column(db.Text)
    motivo_empresa = db.Column(db.Text)
    fecha_respuesta = db.Column(db.DateTime)


class Conexion(db.Model):
    __table_args__ = (
        db.UniqueConstraint("usuario_id", "colega_id", name="unique_conexion"),
    )
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    colega_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship("Usuario", foreign_keys=[usuario_id], backref="conexiones")
    colega = db.relationship("Usuario", foreign_keys=[colega_id])


class Novedad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(40), nullable=False)
    titulo = db.Column(db.String(180), nullable=False)
    detalle = db.Column(db.String(260), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    empresa_id = db.Column(db.Integer, db.ForeignKey("empresa.id"))
    oferta_id = db.Column(db.Integer, db.ForeignKey("oferta.id"))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship("Usuario")
    empresa = db.relationship("Empresa")
    oferta = db.relationship("Oferta")


class Notificacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    titulo = db.Column(db.String(180), nullable=False)
    contenido = db.Column(db.String(320), nullable=False)
    url = db.Column(db.String(255))
    leida = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship("Usuario", backref="notificaciones")


class Mensaje(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    remitente_tipo = db.Column(db.String(20), nullable=False)
    remitente_id = db.Column(db.Integer, nullable=False)
    destinatario_tipo = db.Column(db.String(20), nullable=False)
    destinatario_id = db.Column(db.Integer, nullable=False)
    postulacion_id = db.Column(db.Integer, db.ForeignKey("postulacion.id"), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    leido = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    postulacion = db.relationship(
        "Postulacion",
        backref=db.backref("mensajes", cascade="all, delete-orphan"),
    )


class SesionMentoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    postulacion_id = db.Column(db.Integer, db.ForeignKey("postulacion.id"), nullable=False)
    fecha_programada = db.Column(db.DateTime, default=datetime.utcnow)
    objetivo = db.Column(db.Text, nullable=False)
    avances = db.Column(db.Text)
    evaluacion = db.Column(db.Text)
    completada = db.Column(db.Boolean, default=False)

    postulacion = db.relationship(
        "Postulacion",
        backref=db.backref("sesiones_mentoria", cascade="all, delete-orphan"),
    )


class ResenaEmpresa(db.Model):
    __table_args__ = (
        db.UniqueConstraint("empresa_id", "usuario_id", name="unique_resena_empresa"),
    )
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey("empresa.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    calificacion = db.Column(db.Integer, default=5)
    comentario = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    empresa = db.relationship("Empresa", backref="resenas")
    usuario = db.relationship("Usuario")


class Institucion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(180), nullable=False)
    rut = db.Column(db.String(40))
    tipo = db.Column(db.String(80), default="Liceo TP")
    admin_email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Practica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    postulacion_id = db.Column(db.Integer, db.ForeignKey("postulacion.id"), unique=True, nullable=False)
    institucion_id = db.Column(db.Integer, db.ForeignKey("institucion.id"))
    estado = db.Column(db.String(80), default="Pendiente aprobacion")
    fecha_inicio = db.Column(db.String(20))
    fecha_fin = db.Column(db.String(20))
    horas_objetivo = db.Column(db.Integer, default=450)
    horas_registradas = db.Column(db.Integer, default=0)
    supervisor_liceo = db.Column(db.String(120))
    convenio_digital = db.Column(db.Text)
    evaluacion_empresa = db.Column(db.Text)
    certificado_codigo = db.Column(db.String(80))
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow)

    postulacion = db.relationship(
        "Postulacion",
        backref=db.backref("practica", uselist=False, cascade="all, delete-orphan"),
    )
    institucion = db.relationship("Institucion", backref="practicas")

    @property
    def progreso(self):
        if not self.horas_objetivo:
            return 0
        return min(100, int((self.horas_registradas / self.horas_objetivo) * 100))


class SeguimientoPractica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    practica_id = db.Column(db.Integer, db.ForeignKey("practica.id"), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    horas = db.Column(db.Integer, default=0)
    actividad = db.Column(db.Text, nullable=False)
    evaluacion = db.Column(db.Text)
    validado = db.Column(db.Boolean, default=False)

    practica = db.relationship(
        "Practica",
        backref=db.backref("seguimientos", cascade="all, delete-orphan"),
    )


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


ESPECIALIDADES = [
    "Contabilidad",
    "Recursos Humanos",
    "Logistica",
    "Programacion",
    "Administracion",
]
COMUNAS = [
    "San Ramon",
    "La Pintana",
    "El Bosque",
    "La Granja",
    "Pedro Aguirre Cerda",
    "Lo Espejo",
    "San Miguel",
    "Santiago",
]
MODALIDADES = ["Presencial", "Hibrida", "Remota"]
JORNADAS = ["Part-time", "Full-time", "Practica remunerada", "Flexible"]
TIPOS_OFERTA = ["Empleo", "Practica"]
ESTADOS_FINALES_POSTULACION = {"Aceptado", "Rechazado"}
COMUNA_COORDS = {
    "San Ramon": [-33.5384, -70.6414],
    "La Pintana": [-33.5833, -70.6333],
    "El Bosque": [-33.5667, -70.6750],
    "La Granja": [-33.5431, -70.6250],
    "Pedro Aguirre Cerda": [-33.4928, -70.6744],
    "Lo Espejo": [-33.5211, -70.6894],
    "San Miguel": [-33.4857, -70.6494],
    "Santiago": [-33.4489, -70.6693],
}
TYPING_TTL_SECONDS = 4
REALTIME_INTERVAL_SECONDS = 1
TYPING_STATE = {}


def current_empresa():
    empresa_id = session.get("empresa_id")
    if not empresa_id:
        return None
    return db.session.get(Empresa, empresa_id)


def current_institucion():
    institucion_id = session.get("institucion_id")
    if not institucion_id:
        return None
    return db.session.get(Institucion, institucion_id)


def realtime_identity():
    if current_user.is_authenticated:
        return ("usuario", current_user.id, current_user.nombre_completo)
    empresa = current_empresa()
    if empresa:
        return ("empresa", empresa.id, empresa.nombre)
    institucion = current_institucion()
    if institucion:
        return ("institucion", institucion.id, institucion.nombre)
    return None


def empresa_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_empresa():
            flash("Ingresa como empresa.", "info")
            return redirect(url_for("empresa_login"))
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("admin_ok"):
            flash("Acceso admin requerido.", "info")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapper


def institucion_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_institucion():
            flash("Ingresa como institucion.", "info")
            return redirect(url_for("institucion_login"))
        return view(*args, **kwargs)
    return wrapper


def add_novedad(tipo, titulo, detalle, usuario=None, empresa=None, oferta=None):
    db.session.add(
        Novedad(
            tipo=tipo,
            titulo=titulo,
            detalle=detalle,
            usuario_id=usuario.id if usuario else None,
            empresa_id=empresa.id if empresa else None,
            oferta_id=oferta.id if oferta else None,
        )
    )


def quitar_acentos(texto):
    normalizado = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in normalizado if not unicodedata.combining(c))


def tokenizar(texto):
    limpio = quitar_acentos(texto).lower()
    partes = re.split(r"[,;\n/|]+", limpio)
    tokens = []
    for parte in partes:
        parte = re.sub(r"[^a-z0-9+#. ]", " ", parte).strip()
        if parte:
            tokens.append(re.sub(r"\s+", " ", parte))
    return tokens


def habilidades_usuario(usuario):
    campos = [
        usuario.habilidades,
        usuario.habilidades_tecnicas,
        usuario.habilidades_blandas,
        usuario.herramientas,
        usuario.certificaciones,
        usuario.especialidad,
    ]
    habilidades = set()
    for campo in campos:
        habilidades.update(tokenizar(campo or ""))
    return habilidades


def calcular_match(usuario, oferta):
    requisitos = tokenizar(oferta.requisitos or "")
    if not requisitos:
        return 100 if usuario.especialidad == oferta.especialidad_req else 70
    habilidades = habilidades_usuario(usuario)
    coincidencias = [req for req in requisitos if req in habilidades or any(req in h or h in req for h in habilidades)]
    base = int((len(coincidencias) / len(requisitos)) * 100)
    if usuario.especialidad == oferta.especialidad_req:
        base = min(100, base + 15)
    if usuario.comuna == oferta.comuna:
        base = min(100, base + 5)
    return base


def habilidades_faltantes(usuario, oferta):
    habilidades = habilidades_usuario(usuario)
    faltantes = []
    for requisito in oferta.requisitos_lista:
        token = tokenizar(requisito)
        clave = token[0] if token else requisito.lower()
        if clave not in habilidades and not any(clave in h or h in clave for h in habilidades):
            faltantes.append(requisito)
    return faltantes


def ofertas_ordenadas_para(usuario, ofertas):
    return sorted(
        ofertas,
        key=lambda oferta: (calcular_match(usuario, oferta), oferta.fecha_publicacion or datetime.min),
        reverse=True,
    )


def distancia_km(origen, destino):
    lat1, lon1 = origen
    lat2, lon2 = destino
    radio_tierra = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return 2 * radio_tierra * math.asin(math.sqrt(a))


def enviar_email(usuario, asunto, contenido):
    if not app.config["SMTP_HOST"] or not usuario.email:
        return
    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = app.config["MAIL_FROM"]
    mensaje["To"] = usuario.email
    mensaje.set_content(contenido)
    try:
        with smtplib.SMTP(app.config["SMTP_HOST"], app.config["SMTP_PORT"], timeout=8) as smtp:
            smtp.starttls()
            if app.config["SMTP_USER"]:
                smtp.login(app.config["SMTP_USER"], app.config["SMTP_PASSWORD"])
            smtp.send_message(mensaje)
    except OSError:
        app.logger.info("No se pudo enviar email a %s", usuario.email)


def add_notificacion(usuario, tipo, titulo, contenido, url=None, email=False):
    db.session.add(
        Notificacion(
            usuario_id=usuario.id,
            tipo=tipo,
            titulo=titulo,
            contenido=contenido,
            url=url,
        )
    )
    if email:
        enviar_email(usuario, titulo, contenido)


def notificar_oferta_compatible(oferta):
    usuarios = Usuario.query.filter_by(especialidad=oferta.especialidad_req).all()
    for usuario in usuarios:
        match = calcular_match(usuario, oferta)
        if match >= 55:
            add_notificacion(
                usuario,
                "oferta",
                "Nueva oferta compatible",
                f"{oferta.empresa.nombre} publico {oferta.titulo} con {match}% de compatibilidad.",
                url=url_for("feed"),
            )


def ensure_practica(postulacion):
    if not postulacion.oferta.es_practica:
        return None
    if postulacion.practica:
        return postulacion.practica
    institucion = Institucion.query.first()
    practica = Practica(
        postulacion_id=postulacion.id,
        institucion_id=institucion.id if institucion else None,
        fecha_inicio=postulacion.oferta.fecha_inicio,
        fecha_fin=postulacion.oferta.fecha_fin,
        horas_objetivo=postulacion.oferta.horas_practica or 450,
        convenio_digital=postulacion.oferta.convenio_digital,
        certificado_codigo=f"NEXOTP-{postulacion.id:05d}",
    )
    db.session.add(practica)
    return practica


def ensure_mentoria_inicial(postulacion):
    if not postulacion.oferta.incluye_mentoria or postulacion.sesiones_mentoria:
        return None
    sesion = SesionMentoria(
        postulacion_id=postulacion.id,
        fecha_programada=datetime.utcnow() + timedelta(days=7),
        objetivo="Alinear expectativas, revisar objetivos de aprendizaje y definir primeros pasos.",
    )
    db.session.add(sesion)
    return sesion


def postulaciones_empresa(empresa):
    return (
        Postulacion.query.join(Oferta, Postulacion.oferta_id == Oferta.id)
        .filter(Oferta.empresa_id == empresa.id)
    )


def puede_resenar(usuario, empresa):
    return (
        Postulacion.query.join(Oferta, Postulacion.oferta_id == Oferta.id)
        .filter(
            Postulacion.usuario_id == usuario.id,
            Oferta.empresa_id == empresa.id,
            Postulacion.estado == "Aceptado",
        )
        .first()
        is not None
    )


def postulacion_esta_resuelta(postulacion):
    return postulacion.estado in ESTADOS_FINALES_POSTULACION


def postulacion_permite_mensajes(postulacion):
    return postulacion.estado != "Rechazado"


def aceptados_oferta(oferta, excluir_postulacion_id=None):
    query = Postulacion.query.filter_by(oferta_id=oferta.id, estado="Aceptado")
    if excluir_postulacion_id:
        query = query.filter(Postulacion.id != excluir_postulacion_id)
    return query.count()


def cupos_disponibles_oferta(oferta, excluir_postulacion_id=None):
    vacantes = max(1, oferta.vacantes or 1)
    return max(0, vacantes - aceptados_oferta(oferta, excluir_postulacion_id))


def puede_aceptar_postulacion(postulacion):
    if postulacion.estado == "Aceptado":
        return True
    return cupos_disponibles_oferta(postulacion.oferta, postulacion.id) > 0


def entero_positivo(valor, defecto=1, minimo=1):
    try:
        return max(minimo, int(valor))
    except (TypeError, ValueError):
        return defecto


def limpiar_estados_escritura():
    ahora = time.time()
    expirados = [clave for clave, valor in TYPING_STATE.items() if valor["expires_at"] <= ahora]
    for clave in expirados:
        TYPING_STATE.pop(clave, None)


def registrar_escritura(postulacion, actor_tipo, actor_id, actor_nombre):
    limpiar_estados_escritura()
    clave = f"{postulacion.id}:{actor_tipo}:{actor_id}"
    TYPING_STATE[clave] = {
        "postulacion_id": postulacion.id,
        "actor_tipo": actor_tipo,
        "actor_id": actor_id,
        "actor_nombre": actor_nombre,
        "expires_at": time.time() + TYPING_TTL_SECONDS,
    }


def obtener_escritura_activa(postulacion, actor_tipo, actor_id):
    limpiar_estados_escritura()
    activos = []
    for valor in TYPING_STATE.values():
        if valor["postulacion_id"] != postulacion.id:
            continue
        if valor["actor_tipo"] == actor_tipo and valor["actor_id"] == actor_id:
            continue
        activos.append({"tipo": valor["actor_tipo"], "nombre": valor["actor_nombre"]})
    return activos


def nombre_remitente(mensaje):
    if mensaje.remitente_tipo == "empresa":
        return mensaje.postulacion.oferta.empresa.nombre
    return mensaje.postulacion.usuario.nombre_completo


def serializar_mensaje(mensaje, actor_tipo, actor_id):
    return {
        "id": mensaje.id,
        "autor": nombre_remitente(mensaje),
        "remitente_tipo": mensaje.remitente_tipo,
        "contenido": mensaje.contenido,
        "fecha": mensaje.fecha.strftime("%d-%m-%Y %H:%M"),
        "own": mensaje.remitente_tipo == actor_tipo and mensaje.remitente_id == actor_id,
    }


def serializar_notificacion(notificacion):
    return {
        "id": notificacion.id,
        "titulo": notificacion.titulo,
        "contenido": notificacion.contenido,
        "url": notificacion.url,
        "leida": notificacion.leida,
        "fecha": notificacion.fecha.strftime("%d-%m-%Y %H:%M"),
    }


def conversacion_payload(postulacion, actor_tipo, actor_id):
    mensajes = sorted(postulacion.mensajes, key=lambda mensaje: mensaje.fecha)
    return {
        "postulacion_id": postulacion.id,
        "mensajes": [serializar_mensaje(mensaje, actor_tipo, actor_id) for mensaje in mensajes],
        "typing": obtener_escritura_activa(postulacion, actor_tipo, actor_id),
        "estado": postulacion.estado,
    }


def notificaciones_payload(actor_tipo, actor_id):
    if actor_tipo != "usuario":
        return {"unread": 0, "items": []}
    items = (
        Notificacion.query.filter_by(usuario_id=actor_id, leida=False)
        .order_by(Notificacion.fecha.desc())
        .limit(15)
        .all()
    )
    unread = Notificacion.query.filter_by(usuario_id=actor_id, leida=False).count()
    return {"unread": unread, "items": [serializar_notificacion(item) for item in items]}


def respuesta_json_si_fetch(payload, redirect_url, status=200):
    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify(payload), status
    return redirect(redirect_url)


def seed_data():
    if Empresa.query.count() > 0:
        if Institucion.query.count() == 0:
            institucion = Institucion(
                nombre="Liceo Comercial Vate Vicente Huidobro",
                rut="60.000.000-0",
                tipo="Liceo TP / PTECH IBM",
                admin_email="liceo@nexotp.cl",
            )
            institucion.set_password("liceo123")
            db.session.add(institucion)
            db.session.commit()
        return

    empresas = [
        {
            "nombre": "DevSur Soluciones",
            "email": "empresa@nexotp.cl",
            "password": "empresa123",
            "rubro": "Tecnologia",
            "descripcion": "Desarrollo web para PYMEs.",
            "ubicacion": "San Ramon",
            "contacto": "talento@devsur.cl",
            "web": "https://devsur.cl",
            "logo_inicial": "DS",
            "color": "#2563eb",
            "amigable_tp": True,
            "ofertas": [
                ("Desarrollador web junior", "HTML, CSS y JavaScript en proyectos reales.", "Programacion", "San Ramon", "Hibrida", "Part-time", "$280.000 - $360.000", "HTML/CSS;JavaScript basico;Portafolio escolar"),
                ("QA y soporte web", "Pruebas funcionales y soporte inicial.", "Programacion", "San Ramon", "Remota", "Practica remunerada", "$180.000 - $240.000", "Planillas;Documentacion;Comunicacion"),
            ],
        },
        {
            "nombre": "ContaFacil Chile",
            "email": "contafacil@nexotp.cl",
            "password": "empresa123",
            "rubro": "Contabilidad",
            "descripcion": "Servicios tributarios para pequenas empresas.",
            "ubicacion": "Santiago",
            "contacto": "seleccion@contafacil.cl",
            "web": "https://contafacil.cl",
            "logo_inicial": "CF",
            "color": "#0f766e",
            "amigable_tp": True,
            "ofertas": [
                ("Asistente contable inicial", "Registro documental y apoyo en conciliaciones.", "Contabilidad", "Santiago", "Presencial", "Part-time", "$260.000 - $320.000", "Excel basico;Documentos tributarios;Orden"),
            ],
        },
        {
            "nombre": "LogiSur Distribucion",
            "email": "logisur@nexotp.cl",
            "password": "empresa123",
            "rubro": "Logistica",
            "descripcion": "Distribucion y bodega en el sector sur.",
            "ubicacion": "El Bosque",
            "contacto": "rrhh@logisur.cl",
            "web": "https://logisur.cl",
            "logo_inicial": "LS",
            "color": "#c2410c",
            "amigable_tp": True,
            "ofertas": [
                ("Auxiliar de inventario digital", "Control de stock y conteos ciclicos.", "Logistica", "El Bosque", "Presencial", "Full-time", "$430.000 - $520.000", "Inventario;Computador basico;Trabajo en equipo"),
            ],
        },
    ]

    for data in empresas:
        ofertas = data.pop("ofertas")
        password = data.pop("password")
        empresa = Empresa(**data)
        empresa.set_password(password)
        db.session.add(empresa)
        db.session.flush()
        for titulo, desc, esp, comuna, mod, jornada, sueldo, req in ofertas:
            tipo = "Practica" if "Practica" in jornada else "Empleo"
            oferta = Oferta(
                empresa_id=empresa.id,
                titulo=titulo,
                descripcion=desc,
                especialidad_req=esp,
                comuna=comuna,
                modalidad=mod,
                jornada=jornada,
                tipo=tipo,
                sueldo=sueldo,
                requisitos=req,
                fecha_inicio="2026-11-04" if tipo == "Practica" else "",
                fecha_fin="2027-02-27" if tipo == "Practica" else "",
                mentor_nombre="Francisca Rojas" if tipo == "Practica" else "Carlos Vega",
                mentor_cargo="Mentora de practica" if tipo == "Practica" else "Tutor senior",
                mentor_email=f"mentor@{empresa.email.split('@')[-1]}",
                mentor_bio="Profesional asignado para acompanar el desarrollo tecnico y la insercion laboral.",
                convenio_digital="Convenio empresa-liceo listo para revision institucional." if tipo == "Practica" else "",
            )
            db.session.add(oferta)
            db.session.flush()
            add_novedad("oferta", titulo, f"{empresa.nombre} publico una oferta.", empresa=empresa, oferta=oferta)

    usuarios = [
        ("Camila", "Munoz", "demo@nexotp.cl", "Programacion", "San Ramon", "HTML, CSS, JavaScript, SQLite"),
        ("Joaquin", "Perez", "joaquin@nexotp.cl", "Logistica", "El Bosque", "Inventario, despacho, Excel"),
        ("Jheimy", "Tolentino", "jheimy@nexotp.cl", "Recursos Humanos", "La Pintana", "Contratos, entrevistas, planillas"),
    ]
    for nombre, apellido, email, especialidad, comuna, habilidades in usuarios:
        usuario = Usuario(
            nombre=nombre,
            apellido=apellido,
            email=email,
            especialidad=especialidad,
            liceo="Liceo Comercial Vate Vicente Huidobro",
            comuna=comuna,
            disponibilidad="Part-time",
            modalidad_preferida="Hibrida",
            sobre_mi="Egresado TP en busca de primera experiencia.",
            perfil_profesional=f"Egresado tecnico-profesional de {especialidad}, orientado a aprender en entornos reales.",
            experiencia_resumen="Experiencia escolar en proyectos aplicados y practicas guiadas.",
            objetivo_profesional="Obtener una primera experiencia laboral con mentoria y crecimiento tecnico.",
            habilidades=habilidades,
            habilidades_tecnicas=habilidades,
            habilidades_blandas="Trabajo en equipo, responsabilidad, comunicacion",
            idiomas="Espanol: Nativo; Ingles: Basico",
            herramientas="Google Workspace, Excel, Git basico",
            certificaciones=f"Especialidad {especialidad} TP",
            carrera_titulo=f"Tecnico nivel medio en {especialidad}",
            institucion="Liceo Comercial Vate Vicente Huidobro",
            anio_ingreso="2023",
            anio_egreso="2025",
            cursos_relevantes="PTECH IBM; Empleabilidad y emprendimiento",
            experiencia_laboral="Sin experiencia formal. Proyectos escolares y simulaciones tecnicas.",
            proyectos="Portafolio escolar: proyecto aplicado de especialidad con documentacion y presentacion.",
            referencias="Referencias disponibles a solicitud.",
        )
        usuario.set_password("demo123")
        db.session.add(usuario)
        db.session.flush()
        add_novedad("perfil", "Nuevo perfil TP", f"{usuario.nombre_completo} se unio a la red.", usuario=usuario)

    institucion = Institucion(
        nombre="Liceo Comercial Vate Vicente Huidobro",
        rut="60.000.000-0",
        tipo="Liceo TP / PTECH IBM",
        admin_email="liceo@nexotp.cl",
    )
    institucion.set_password("liceo123")
    db.session.add(institucion)
    db.session.flush()

    demo = Usuario.query.filter_by(email="demo@nexotp.cl").first()
    practica_demo = Oferta.query.filter_by(titulo="QA y soporte web").first()
    if demo and practica_demo:
        postulacion = Postulacion(
            usuario_id=demo.id,
            oferta_id=practica_demo.id,
            estado="Aceptado",
            mensaje="Me interesa aprender QA en un equipo real.",
            motivo_empresa="Aceptada para iniciar practica con mentoria.",
            fecha_respuesta=datetime.utcnow(),
        )
        db.session.add(postulacion)
        db.session.flush()
        ensure_practica(postulacion)
        ensure_mentoria_inicial(postulacion)
        db.session.add(
            Mensaje(
                remitente_tipo="empresa",
                remitente_id=practica_demo.empresa.id,
                destinatario_tipo="usuario",
                destinatario_id=demo.id,
                postulacion_id=postulacion.id,
                contenido="Hola Camila, coordinemos tu entrevista tecnica esta semana.",
            )
        )
        add_notificacion(
            demo,
            "postulacion",
            "Postulacion aceptada",
            "DevSur acepto tu postulacion y dejo un mensaje.",
            url="/postulado",
        )
        db.session.add(
            ResenaEmpresa(
                empresa_id=practica_demo.empresa.id,
                usuario_id=demo.id,
                calificacion=5,
                comentario="Proceso claro, con mentoria real y buena comunicacion.",
            )
        )
    db.session.commit()


COLUMN_MIGRATIONS = {
    "empresa": {
        "foto_url": "VARCHAR(255)",
        "amigable_tp": "BOOLEAN DEFAULT 1",
    },
    "oferta": {
        "tipo": "VARCHAR(40) DEFAULT 'Empleo'",
        "mentor_nombre": "VARCHAR(120)",
        "mentor_cargo": "VARCHAR(120)",
        "mentor_email": "VARCHAR(150)",
        "mentor_bio": "TEXT",
        "fecha_inicio": "VARCHAR(20)",
        "fecha_fin": "VARCHAR(20)",
        "convenio_digital": "TEXT",
        "horas_practica": "INTEGER DEFAULT 450",
    },
}


def ensure_schema_columns():
    inspector = inspect(db.engine)
    with db.engine.begin() as connection:
        for table, columns in COLUMN_MIGRATIONS.items():
            if not inspector.has_table(table):
                continue
            existing = {column["name"] for column in inspector.get_columns(table)}
            for column_name, ddl in columns.items():
                if column_name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_name} {ddl}"))


def schema_needs_rebuild():
    inspector = inspect(db.engine)
    required = {
        "usuario": {
            "telefono",
            "pais",
            "foto_url",
            "fecha_nacimiento",
            "perfil_profesional",
            "experiencia_resumen",
            "objetivo_profesional",
            "habilidades",
            "habilidades_tecnicas",
            "habilidades_blandas",
            "idiomas",
            "herramientas",
            "certificaciones",
            "carrera_titulo",
            "institucion",
            "anio_ingreso",
            "anio_egreso",
            "cursos_relevantes",
            "experiencia_laboral",
            "proyectos",
            "referencias",
            "modalidad_preferida",
        },
        "empresa": {"email", "password_hash", "contacto", "web"},
        "oferta": {"comuna", "sueldo", "vacantes", "incluye_mentoria", "requisitos"},
        "postulacion": {"mensaje", "motivo_empresa", "fecha_respuesta"},
        "conexion": {"usuario_id", "colega_id"},
        "novedad": {"tipo", "titulo", "detalle"},
    }
    for table, columns in required.items():
        if not inspector.has_table(table):
            return True
        existing = {column["name"] for column in inspector.get_columns(table)}
        if not columns.issubset(existing):
            return True
    return False


def init_database():
    try:
        db.create_all()
        ensure_schema_columns()
        seed_data()
    except OperationalError:
        db.session.rollback()
        db.drop_all()
        db.create_all()
        seed_data()


@app.context_processor
def inject_globals():
    unread = 0
    mostrar_onboarding = False
    if current_user.is_authenticated:
        unread = Notificacion.query.filter_by(usuario_id=current_user.id, leida=False).count()
        mostrar_onboarding = session.pop("show_onboarding", False)
    return {
        "app_name": APP_NAME,
        "especialidades": ESPECIALIDADES,
        "comunas": COMUNAS,
        "modalidades": MODALIDADES,
        "jornadas": JORNADAS,
        "tipos_oferta": TIPOS_OFERTA,
        "empresa_actual": current_empresa(),
        "institucion_actual": current_institucion(),
        "notificaciones_pendientes": unread,
        "mostrar_onboarding": mostrar_onboarding,
    }


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("feed"))
    stats = {
        "empresas": Empresa.query.count(),
        "ofertas": Oferta.query.filter_by(activa=True).count(),
        "egresados": Usuario.query.count(),
    }
    ofertas = Oferta.query.filter_by(activa=True).order_by(Oferta.fecha_publicacion.desc()).limit(3)
    novedades = Novedad.query.order_by(Novedad.fecha.desc()).limit(4)
    return render_template("index.html", stats=stats, ofertas=ofertas, novedades=novedades)


@app.route("/dashboard")
@login_required
def dashboard():
    postulaciones = Postulacion.query.filter_by(usuario_id=current_user.id).order_by(Postulacion.fecha.desc()).all()
    respondidas = [p for p in postulaciones if p.estado in {"Aceptado", "Rechazado"}]
    aceptadas = [p for p in postulaciones if p.estado == "Aceptado"]
    tasa_aceptacion = int((len(aceptadas) / len(respondidas)) * 100) if respondidas else 0

    semanas = []
    hoy = datetime.utcnow()
    for index_semana in range(5, -1, -1):
        inicio = hoy - timedelta(weeks=index_semana)
        fin = inicio + timedelta(days=7)
        total = sum(1 for p in postulaciones if inicio <= p.fecha < fin)
        semanas.append({"label": inicio.strftime("%d-%m"), "total": total})

    ids_postuladas = {p.oferta_id for p in postulaciones}
    ofertas_base = Oferta.query.filter_by(activa=True).all()
    recomendadas = [
        oferta for oferta in ofertas_ordenadas_para(current_user, ofertas_base)
        if oferta.id not in ids_postuladas
    ][:5]
    match_map = {oferta.id: calcular_match(current_user, oferta) for oferta in recomendadas}

    pares = Usuario.query.filter(
        Usuario.id != current_user.id,
        Usuario.especialidad == current_user.especialidad,
    ).all()
    total_pares = len(pares)
    promedio_postulaciones = 0
    tasa_pares = 0
    if pares:
        total_postulaciones_pares = sum(len(usuario.postulaciones) for usuario in pares)
        promedio_postulaciones = round(total_postulaciones_pares / len(pares), 1)
        respuestas_pares = [
            p for usuario in pares for p in usuario.postulaciones if p.estado in {"Aceptado", "Rechazado"}
        ]
        aceptadas_pares = [p for p in respuestas_pares if p.estado == "Aceptado"]
        tasa_pares = int((len(aceptadas_pares) / len(respuestas_pares)) * 100) if respuestas_pares else 0

    return render_template(
        "dashboard.html",
        postulaciones=postulaciones,
        respondidas=respondidas,
        tasa_aceptacion=tasa_aceptacion,
        semanas=semanas,
        recomendadas=recomendadas,
        match_map=match_map,
        total_pares=total_pares,
        promedio_postulaciones=promedio_postulaciones,
        tasa_pares=tasa_pares,
    )


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for("feed"))
    if request.method == "POST":
        usuario = Usuario(
            nombre=request.form.get("nombre", "").strip(),
            apellido=request.form.get("apellido", "").strip(),
            email=request.form.get("email", "").strip().lower(),
            especialidad=request.form.get("especialidad", "").strip(),
            comuna=request.form.get("comuna", "").strip(),
            pais=request.form.get("pais", "Chile").strip() or "Chile",
            telefono=request.form.get("telefono", "").strip(),
            liceo=request.form.get("liceo", "").strip() or "Liceo Comercial Vate Vicente Huidobro",
            disponibilidad=request.form.get("disponibilidad", "Flexible"),
            modalidad_preferida=request.form.get("modalidad_preferida", "Hibrida"),
            habilidades=request.form.get("habilidades", "").strip(),
            habilidades_tecnicas=request.form.get("habilidades", "").strip(),
            sobre_mi=request.form.get("sobre_mi", "").strip(),
            perfil_profesional=request.form.get("sobre_mi", "").strip(),
        )
        password = request.form.get("password", "")
        if not all([usuario.nombre, usuario.apellido, usuario.email, usuario.especialidad, usuario.comuna, password]):
            flash("Completa los campos obligatorios.", "error")
            return redirect(url_for("registro"))
        if len(password) < 6:
            flash("La contrasena debe tener al menos 6 caracteres.", "error")
            return redirect(url_for("registro"))
        usuario.set_password(password)
        try:
            db.session.add(usuario)
            db.session.flush()
            add_novedad("perfil", "Nuevo perfil TP", f"{usuario.nombre_completo} se unio a la red.", usuario=usuario)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Ese correo ya esta registrado.", "error")
            return redirect(url_for("registro"))
        login_user(usuario)
        session["show_onboarding"] = True
        return redirect(url_for("feed"))
    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("feed"))
    if request.method == "POST":
        usuario = Usuario.query.filter_by(email=request.form.get("email", "").strip().lower()).first()
        if usuario and usuario.check_password(request.form.get("password", "")):
            session.pop("empresa_id", None)
            login_user(usuario)
            return redirect(url_for("feed"))
        flash("Correo o contrasena incorrectos.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    session.pop("empresa_id", None)
    session.pop("institucion_id", None)
    session.pop("admin_ok", None)
    return redirect(url_for("index"))


@app.route("/feed")
@login_required
def feed():
    query = Oferta.query.filter_by(activa=True)
    especialidad = request.args.get("especialidad", "")
    modalidad = request.args.get("modalidad", "")
    comuna = request.args.get("comuna", "")
    busqueda = request.args.get("q", "").strip()
    if especialidad:
        query = query.filter_by(especialidad_req=especialidad)
    if modalidad:
        query = query.filter_by(modalidad=modalidad)
    if comuna:
        query = query.filter_by(comuna=comuna)
    if busqueda:
        like = f"%{busqueda}%"
        query = query.filter(or_(Oferta.titulo.ilike(like), Oferta.descripcion.ilike(like), Oferta.requisitos.ilike(like)))
    postulaciones_usuario = Postulacion.query.filter_by(usuario_id=current_user.id).all()
    mis_postulaciones = {p.oferta_id: p for p in postulaciones_usuario}
    if mis_postulaciones:
        query = query.filter(~Oferta.id.in_(mis_postulaciones.keys()))
    ofertas = ofertas_ordenadas_para(current_user, query.order_by(Oferta.fecha_publicacion.desc()).all())
    match_map = {oferta.id: calcular_match(current_user, oferta) for oferta in ofertas}
    faltantes_map = {oferta.id: habilidades_faltantes(current_user, oferta)[:3] for oferta in ofertas}
    novedades = Novedad.query.order_by(Novedad.fecha.desc()).limit(12)
    return render_template(
        "feed.html",
        ofertas=ofertas,
        mis_postulaciones=mis_postulaciones,
        match_map=match_map,
        faltantes_map=faltantes_map,
        novedades=novedades,
        filtros={"especialidad": especialidad, "modalidad": modalidad, "comuna": comuna, "q": busqueda},
    )


@app.route("/postular/<int:oferta_id>", methods=["POST"])
@login_required
def postular(oferta_id):
    oferta = db.session.get(Oferta, oferta_id)
    if not oferta or not oferta.activa:
        return jsonify({"ok": False, "message": "Oferta no disponible."}), 404
    if Postulacion.query.filter_by(usuario_id=current_user.id, oferta_id=oferta_id).first():
        return jsonify({"ok": False, "message": "Ya postulaste."}), 409
    postulacion = Postulacion(
        usuario_id=current_user.id,
        oferta_id=oferta.id,
        mensaje=request.form.get("mensaje", "").strip(),
    )
    db.session.add(postulacion)
    db.session.flush()
    ensure_practica(postulacion)
    add_notificacion(
        current_user,
        "postulacion",
        "Postulacion enviada",
        f"Tu postulacion a {oferta.titulo} quedo registrada.",
        url=url_for("postulado"),
    )
    add_novedad("postulacion", "Nueva postulacion", f"{current_user.nombre_completo} postulo a {oferta.titulo}.", usuario=current_user, empresa=oferta.empresa, oferta=oferta)
    db.session.commit()
    return jsonify({"ok": True, "message": "Postulacion enviada."})


@app.route("/perfil")
@login_required
def perfil():
    postulaciones = Postulacion.query.filter_by(usuario_id=current_user.id).order_by(Postulacion.fecha.desc()).all()
    conexiones = Conexion.query.filter_by(usuario_id=current_user.id).all()
    return render_template("perfil.html", postulaciones=postulaciones, conexiones=conexiones)


def pdf_simple(lines):
    escaped_lines = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines]
    stream = ["BT", "/F1 12 Tf", "50 760 Td"]
    for idx, line in enumerate(escaped_lines):
        if idx:
            stream.append("0 -18 Td")
        stream.append(f"({line[:92]}) Tj")
    stream.append("ET")
    content = "\n".join(stream).encode("latin-1", "ignore")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{idx} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return bytes(pdf)


def generar_cv_pdf(usuario):
    perfil_url = url_for("perfil_publico", usuario_id=usuario.id, _external=True)
    lines = [
        f"{usuario.nombre_completo}",
        f"{usuario.especialidad} - {usuario.comuna}, {usuario.pais}",
        f"Email: {usuario.email} | Telefono: {usuario.telefono or 'No informado'}",
        "",
        "Perfil profesional",
        usuario.perfil_profesional or usuario.sobre_mi or "Egresado TP en busqueda de primera experiencia.",
        "",
        "Objetivo",
        usuario.objetivo_profesional or "Insertarse laboralmente y seguir aprendiendo con acompanamiento.",
        "",
        "Habilidades tecnicas",
        usuario.habilidades_tecnicas or usuario.habilidades or "No informado",
        "",
        "Habilidades blandas",
        usuario.habilidades_blandas or "Responsabilidad, comunicacion y trabajo en equipo.",
        "",
        "Proyectos",
        usuario.proyectos or "Proyectos escolares disponibles en el perfil publico.",
        "",
        f"Perfil publico / QR: {perfil_url}",
    ]
    try:
        from reportlab.graphics import renderPDF
        from reportlab.graphics.barcode import qr
        from reportlab.graphics.shapes import Drawing
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        return pdf_simple(lines)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 54
    c.setFont("Helvetica-Bold", 22)
    c.drawString(48, y, usuario.nombre_completo)
    y -= 24
    c.setFont("Helvetica", 11)
    c.drawString(48, y, f"{usuario.especialidad} | {usuario.comuna}, {usuario.pais}")
    y -= 18
    c.drawString(48, y, f"{usuario.email} | {usuario.telefono or 'Telefono no informado'}")
    y -= 30
    secciones = [
        ("Perfil profesional", usuario.perfil_profesional or usuario.sobre_mi),
        ("Objetivo", usuario.objetivo_profesional),
        ("Formacion", f"{usuario.carrera_titulo or usuario.especialidad} - {usuario.institucion or usuario.liceo}"),
        ("Habilidades tecnicas", usuario.habilidades_tecnicas or usuario.habilidades),
        ("Habilidades blandas", usuario.habilidades_blandas),
        ("Herramientas", usuario.herramientas),
        ("Proyectos", usuario.proyectos),
    ]
    for titulo, contenido in secciones:
        if y < 120:
            c.showPage()
            y = height - 54
        c.setFont("Helvetica-Bold", 12)
        c.drawString(48, y, titulo)
        y -= 16
        c.setFont("Helvetica", 10)
        texto = contenido or "No informado"
        for inicio in range(0, len(texto), 95):
            c.drawString(48, y, texto[inicio:inicio + 95])
            y -= 13
        y -= 8
    qr_code = qr.QrCodeWidget(perfil_url)
    drawing = Drawing(92, 92)
    drawing.add(qr_code)
    renderPDF.draw(drawing, c, width - 142, 48)
    c.setFont("Helvetica", 8)
    c.drawRightString(width - 48, 42, "Perfil publico NexoTP")
    c.save()
    return buffer.getvalue()


@app.route("/perfil/cv.pdf")
@login_required
def descargar_cv():
    pdf = generar_cv_pdf(current_user)
    filename = f"CV-{current_user.nombre}-{current_user.apellido}.pdf"
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.route("/u/<int:usuario_id>")
def perfil_publico(usuario_id):
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        return render_template("404.html"), 404
    postulaciones_aceptadas = Postulacion.query.filter_by(usuario_id=usuario.id, estado="Aceptado").all()
    return render_template("perfil_publico.html", usuario=usuario, postulaciones_aceptadas=postulaciones_aceptadas)


@app.route("/postulado")
@login_required
def postulado():
    postulaciones = Postulacion.query.filter_by(usuario_id=current_user.id).order_by(Postulacion.fecha.desc()).all()
    return render_template("postulado.html", postulaciones=postulaciones)


@app.route("/notificaciones", methods=["GET", "POST"])
@login_required
def notificaciones():
    if request.method == "POST":
        Notificacion.query.filter_by(usuario_id=current_user.id).delete()
        db.session.commit()
        flash("Notificaciones marcadas como leidas y eliminadas.", "success")
        return redirect(url_for("notificaciones"))
    Notificacion.query.filter_by(usuario_id=current_user.id, leida=True).delete()
    db.session.commit()
    items = (
        Notificacion.query.filter_by(usuario_id=current_user.id, leida=False)
        .order_by(Notificacion.fecha.desc())
        .all()
    )
    return render_template("notificaciones.html", notificaciones=items)


@app.route("/api/notificaciones/unread")
@login_required
def api_notificaciones_unread():
    total = Notificacion.query.filter_by(usuario_id=current_user.id, leida=False).count()
    return jsonify({"unread": total})


@app.route("/api/mensajes/<int:postulacion_id>")
def api_mensajes(postulacion_id):
    identity = realtime_identity()
    if not identity:
        return jsonify({"ok": False, "message": "No autenticado."}), 401
    actor_tipo, actor_id, _actor_nombre = identity
    empresa = current_empresa() if actor_tipo == "empresa" else None
    postulacion = postulacion_mensajes_autorizada(postulacion_id, empresa)
    if not postulacion:
        return jsonify({"ok": False, "message": "Conversacion no disponible."}), 404
    return jsonify({"ok": True, "conversation": conversacion_payload(postulacion, actor_tipo, actor_id)})


@app.route("/api/typing/<int:postulacion_id>", methods=["POST"])
def api_typing(postulacion_id):
    identity = realtime_identity()
    if not identity:
        return jsonify({"ok": False, "message": "No autenticado."}), 401
    actor_tipo, actor_id, actor_nombre = identity
    empresa = current_empresa() if actor_tipo == "empresa" else None
    postulacion = postulacion_mensajes_autorizada(postulacion_id, empresa)
    if not postulacion:
        return jsonify({"ok": False, "message": "Conversacion no disponible."}), 404
    if not postulacion_permite_mensajes(postulacion):
        return jsonify({"ok": False, "message": "La postulacion fue rechazada; la conversacion esta cerrada."}), 403
    registrar_escritura(postulacion, actor_tipo, actor_id, actor_nombre)
    return jsonify({"ok": True})


@app.route("/api/realtime/stream")
def api_realtime_stream():
    identity = realtime_identity()
    if not identity:
        return Response("No autenticado.", status=401)
    actor_tipo, actor_id, _actor_nombre = identity
    selected_id = request.args.get("postulacion_id", type=int)

    def payload_actual():
        payload = {
            "server_time": datetime.utcnow().isoformat(),
            "notifications": notificaciones_payload(actor_tipo, actor_id),
        }
        if selected_id:
            empresa = current_empresa() if actor_tipo == "empresa" else None
            postulacion = postulacion_mensajes_autorizada(selected_id, empresa)
            if postulacion:
                payload["conversation"] = conversacion_payload(postulacion, actor_tipo, actor_id)
        return payload

    @stream_with_context
    def stream():
        ultimo_payload = None
        while True:
            payload = payload_actual()
            serializado = json.dumps(payload, ensure_ascii=False)
            if serializado != ultimo_payload:
                yield f"event: realtime\ndata: {serializado}\n\n"
                ultimo_payload = serializado
            else:
                yield "event: heartbeat\ndata: {}\n\n"
            time.sleep(REALTIME_INTERVAL_SECONDS)

    return Response(
        stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def postulaciones_con_mensajes_usuario():
    return (
        Postulacion.query.filter_by(usuario_id=current_user.id)
        .order_by(Postulacion.fecha.desc())
        .all()
    )


def postulacion_mensajes_autorizada(postulacion_id, empresa=None):
    postulacion = db.session.get(Postulacion, postulacion_id)
    if not postulacion:
        return None
    if empresa and postulacion.oferta.empresa_id == empresa.id:
        return postulacion
    if current_user.is_authenticated and postulacion.usuario_id == current_user.id:
        return postulacion
    return None


@app.route("/mensajes")
@login_required
def mensajes_usuario():
    postulaciones = postulaciones_con_mensajes_usuario()
    selected_id = request.args.get("postulacion_id", type=int)
    seleccionada = postulacion_mensajes_autorizada(selected_id) if selected_id else (postulaciones[0] if postulaciones else None)
    if seleccionada:
        Mensaje.query.filter_by(
            postulacion_id=seleccionada.id,
            destinatario_tipo="usuario",
            destinatario_id=current_user.id,
            leido=False,
        ).update({"leido": True})
        db.session.commit()
    return render_template(
        "mensajes.html",
        postulaciones=postulaciones,
        seleccionada=seleccionada,
        es_empresa=False,
    )


@app.route("/mensajes/<int:postulacion_id>", methods=["POST"])
@login_required
def enviar_mensaje_usuario(postulacion_id):
    postulacion = postulacion_mensajes_autorizada(postulacion_id)
    if not postulacion:
        flash("Conversacion no disponible.", "error")
        return redirect(url_for("mensajes_usuario"))
    if not postulacion_permite_mensajes(postulacion):
        flash("La postulacion fue rechazada. La conversacion queda cerrada como historial.", "info")
        return respuesta_json_si_fetch(
            {"ok": False, "message": "La postulacion fue rechazada; no se pueden enviar mas mensajes."},
            url_for("mensajes_usuario", postulacion_id=postulacion.id),
            status=403,
        )
    contenido = request.form.get("contenido", "").strip()
    if contenido:
        db.session.add(
            Mensaje(
                remitente_tipo="usuario",
                remitente_id=current_user.id,
                destinatario_tipo="empresa",
                destinatario_id=postulacion.oferta.empresa_id,
                postulacion_id=postulacion.id,
                contenido=contenido,
            )
        )
        db.session.commit()
    TYPING_STATE.pop(f"{postulacion.id}:usuario:{current_user.id}", None)
    return respuesta_json_si_fetch(
        {"ok": True, "message": "Mensaje enviado.", "postulacion_id": postulacion.id},
        url_for("mensajes_usuario", postulacion_id=postulacion.id),
    )


@app.route("/empresa/mensajes")
@empresa_required
def mensajes_empresa():
    empresa = current_empresa()
    postulaciones = postulaciones_empresa(empresa).order_by(Postulacion.fecha.desc()).all()
    selected_id = request.args.get("postulacion_id", type=int)
    seleccionada = postulacion_mensajes_autorizada(selected_id, empresa) if selected_id else (postulaciones[0] if postulaciones else None)
    if seleccionada:
        Mensaje.query.filter_by(
            postulacion_id=seleccionada.id,
            destinatario_tipo="empresa",
            destinatario_id=empresa.id,
            leido=False,
        ).update({"leido": True})
        db.session.commit()
    return render_template(
        "mensajes.html",
        postulaciones=postulaciones,
        seleccionada=seleccionada,
        es_empresa=True,
    )


@app.route("/empresa/mensajes/<int:postulacion_id>", methods=["POST"])
@empresa_required
def enviar_mensaje_empresa(postulacion_id):
    empresa = current_empresa()
    postulacion = postulacion_mensajes_autorizada(postulacion_id, empresa)
    if not postulacion:
        flash("Conversacion no disponible.", "error")
        return redirect(url_for("mensajes_empresa"))
    if not postulacion_permite_mensajes(postulacion):
        flash("La postulacion fue rechazada. La conversacion queda cerrada como historial.", "info")
        return respuesta_json_si_fetch(
            {"ok": False, "message": "La postulacion fue rechazada; no se pueden enviar mas mensajes."},
            url_for("mensajes_empresa", postulacion_id=postulacion.id),
            status=403,
        )
    contenido = request.form.get("contenido", "").strip()
    if contenido:
        db.session.add(
            Mensaje(
                remitente_tipo="empresa",
                remitente_id=empresa.id,
                destinatario_tipo="usuario",
                destinatario_id=postulacion.usuario_id,
                postulacion_id=postulacion.id,
                contenido=contenido,
            )
        )
        add_notificacion(
            postulacion.usuario,
            "mensaje",
            "Nuevo mensaje de empresa",
            f"{empresa.nombre} escribio sobre {postulacion.oferta.titulo}.",
            url=url_for("mensajes_usuario", postulacion_id=postulacion.id),
        )
        db.session.commit()
    TYPING_STATE.pop(f"{postulacion.id}:empresa:{empresa.id}", None)
    return respuesta_json_si_fetch(
        {"ok": True, "message": "Mensaje enviado.", "postulacion_id": postulacion.id},
        url_for("mensajes_empresa", postulacion_id=postulacion.id),
    )


@app.route("/perfil/editar", methods=["GET", "POST"])
@login_required
def editar_perfil():
    if request.method == "POST":
        fields = [
            "nombre",
            "apellido",
            "especialidad",
            "liceo",
            "comuna",
            "pais",
            "telefono",
            "foto_url",
            "fecha_nacimiento",
            "disponibilidad",
            "modalidad_preferida",
            "sobre_mi",
            "perfil_profesional",
            "experiencia_resumen",
            "objetivo_profesional",
            "habilidades",
            "habilidades_tecnicas",
            "habilidades_blandas",
            "idiomas",
            "herramientas",
            "certificaciones",
            "carrera_titulo",
            "institucion",
            "anio_ingreso",
            "anio_egreso",
            "cursos_relevantes",
            "experiencia_laboral",
            "proyectos",
            "referencias",
            "portafolio",
            "linkedin",
        ]
        for field in fields:
            value = request.form.get(field, "").strip()
            setattr(current_user, field, value)
        db.session.commit()
        flash("Perfil actualizado.", "success")
        return redirect(url_for("perfil"))
    return render_template("editar_perfil.html")


@app.route("/red")
@login_required
def red():
    conectados = {c.colega_id for c in current_user.conexiones}
    usuarios = Usuario.query.filter(Usuario.id != current_user.id).order_by(Usuario.fecha_registro.desc()).all()
    return render_template("red.html", usuarios=usuarios, conectados=conectados)


@app.route("/conectar/<int:usuario_id>", methods=["POST"])
@login_required
def conectar(usuario_id):
    colega = db.session.get(Usuario, usuario_id)
    if not colega or colega.id == current_user.id:
        return redirect(url_for("red"))
    if usuario_id not in {c.colega_id for c in current_user.conexiones}:
        db.session.add(Conexion(usuario_id=current_user.id, colega_id=usuario_id))
        add_novedad("conexion", "Nueva conexion", f"{current_user.nombre_completo} agrego a {colega.nombre_completo}.", usuario=current_user)
        db.session.commit()
    return redirect(url_for("red"))


@app.route("/empresas")
@login_required
def empresas():
    return render_template("empresas.html", empresas=Empresa.query.order_by(Empresa.nombre.asc()).all())


@app.route("/empresa/<int:empresa_id>", methods=["GET", "POST"])
def empresa_publica(empresa_id):
    empresa = db.session.get(Empresa, empresa_id)
    if not empresa:
        return render_template("404.html"), 404
    puede_dejar_resena = current_user.is_authenticated and puede_resenar(current_user, empresa)
    if request.method == "POST":
        if not puede_dejar_resena:
            flash("Solo puedes resenar empresas donde fuiste aceptado.", "error")
            return redirect(url_for("empresa_publica", empresa_id=empresa.id))
        comentario = request.form.get("comentario", "").strip()
        calificacion = max(1, min(5, int(request.form.get("calificacion") or 5)))
        if not comentario:
            flash("Escribe un comentario breve.", "error")
            return redirect(url_for("empresa_publica", empresa_id=empresa.id))
        resena = ResenaEmpresa.query.filter_by(empresa_id=empresa.id, usuario_id=current_user.id).first()
        if not resena:
            resena = ResenaEmpresa(empresa_id=empresa.id, usuario_id=current_user.id)
            db.session.add(resena)
        resena.calificacion = calificacion
        resena.comentario = comentario
        resena.fecha = datetime.utcnow()
        db.session.commit()
        flash("Resena guardada.", "success")
        return redirect(url_for("empresa_publica", empresa_id=empresa.id))

    ofertas_activas = Oferta.query.filter_by(empresa_id=empresa.id, activa=True).order_by(Oferta.fecha_publicacion.desc()).all()
    historicas = Oferta.query.filter_by(empresa_id=empresa.id).count()
    postulaciones = postulaciones_empresa(empresa).all()
    aceptadas = [p for p in postulaciones if p.estado == "Aceptado"]
    tasa = int((len(aceptadas) / len(postulaciones)) * 100) if postulaciones else 0
    promedio = 0
    if empresa.resenas:
        promedio = round(sum(r.calificacion for r in empresa.resenas) / len(empresa.resenas), 1)
    return render_template(
        "empresa_publica.html",
        empresa=empresa,
        ofertas_activas=ofertas_activas,
        historicas=historicas,
        aceptadas=aceptadas,
        tasa=tasa,
        promedio=promedio,
        puede_dejar_resena=puede_dejar_resena,
    )


@app.route("/empresa/login", methods=["GET", "POST"])
def empresa_login():
    if request.method == "POST":
        empresa = Empresa.query.filter_by(email=request.form.get("email", "").strip().lower()).first()
        if empresa and empresa.check_password(request.form.get("password", "")):
            logout_user()
            session.pop("institucion_id", None)
            session.pop("admin_ok", None)
            session["empresa_id"] = empresa.id
            return redirect(url_for("empresa_panel"))
        flash("Credenciales de empresa incorrectas.", "error")
    return render_template("empresa_login.html")


@app.route("/empresa/registro", methods=["GET", "POST"])
def empresa_registro():
    if request.method == "POST":
        empresa = Empresa(
            nombre=request.form.get("nombre", "").strip(),
            email=request.form.get("email", "").strip().lower(),
            rubro=request.form.get("rubro", "").strip(),
            descripcion=request.form.get("descripcion", "").strip(),
            ubicacion=request.form.get("ubicacion", "").strip(),
            contacto=request.form.get("contacto", "").strip(),
            web=request.form.get("web", "").strip(),
            foto_url=request.form.get("foto_url", "").strip(),
            amigable_tp=request.form.get("amigable_tp") == "1",
            logo_inicial=request.form.get("nombre", "EM")[:2].upper(),
        )
        password = request.form.get("password", "")
        if not all([empresa.nombre, empresa.email, empresa.rubro, empresa.descripcion, empresa.ubicacion, password]):
            flash("Completa los campos obligatorios.", "error")
            return redirect(url_for("empresa_registro"))
        empresa.set_password(password)
        try:
            db.session.add(empresa)
            db.session.flush()
            add_novedad("empresa", "Nueva empresa", f"{empresa.nombre} se unio a la red.", empresa=empresa)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Ese correo de empresa ya existe.", "error")
            return redirect(url_for("empresa_registro"))
        session["empresa_id"] = empresa.id
        return redirect(url_for("empresa_panel"))
    return render_template("empresa_registro.html")


@app.route("/empresa/panel")
@empresa_required
def empresa_panel():
    empresa = current_empresa()
    estado = request.args.get("estado", "").strip()
    oferta_id_raw = request.args.get("oferta_id", "").strip()
    modalidad = request.args.get("modalidad", "").strip()
    jornada = request.args.get("jornada", "").strip()
    especialidad = request.args.get("especialidad", "").strip()
    q = request.args.get("q", "").strip()
    fecha_desde = request.args.get("fecha_desde", "").strip()
    fecha_hasta = request.args.get("fecha_hasta", "").strip()

    ofertas = (
        Oferta.query.filter_by(empresa_id=empresa.id)
        .order_by(Oferta.fecha_publicacion.desc())
        .all()
    )

    postulaciones_query = (
        Postulacion.query.join(Oferta, Postulacion.oferta_id == Oferta.id)
        .join(Usuario, Postulacion.usuario_id == Usuario.id)
        .filter(Oferta.empresa_id == empresa.id)
    )

    if estado:
        postulaciones_query = postulaciones_query.filter(Postulacion.estado == estado)
    if oferta_id_raw.isdigit():
        postulaciones_query = postulaciones_query.filter(Postulacion.oferta_id == int(oferta_id_raw))
    if modalidad:
        postulaciones_query = postulaciones_query.filter(Oferta.modalidad == modalidad)
    if jornada:
        postulaciones_query = postulaciones_query.filter(Oferta.jornada == jornada)
    if especialidad:
        postulaciones_query = postulaciones_query.filter(Oferta.especialidad_req == especialidad)
    if q:
        like_q = f"%{q}%"
        postulaciones_query = postulaciones_query.filter(
            or_(
                Usuario.nombre.ilike(like_q),
                Usuario.apellido.ilike(like_q),
                Usuario.email.ilike(like_q),
                Oferta.titulo.ilike(like_q),
            )
        )
    if fecha_desde:
        try:
            postulaciones_query = postulaciones_query.filter(
                Postulacion.fecha >= datetime.strptime(fecha_desde, "%Y-%m-%d")
            )
        except ValueError:
            flash("La fecha desde no es valida.", "error")
    if fecha_hasta:
        try:
            postulaciones_query = postulaciones_query.filter(
                Postulacion.fecha < datetime.strptime(fecha_hasta, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            )
        except ValueError:
            flash("La fecha hasta no es valida.", "error")

    postulaciones = postulaciones_query.order_by(Postulacion.fecha.desc()).all()
    match_map = {p.id: calcular_match(p.usuario, p.oferta) for p in postulaciones}
    cupos_map = {p.id: cupos_disponibles_oferta(p.oferta) for p in postulaciones}

    return render_template(
        "empresa_panel.html",
        empresa=empresa,
        ofertas=ofertas,
        postulaciones=postulaciones,
        match_map=match_map,
        cupos_map=cupos_map,
        estados_finales=ESTADOS_FINALES_POSTULACION,
        filtros={
            "estado": estado,
            "oferta_id": oferta_id_raw,
            "modalidad": modalidad,
            "jornada": jornada,
            "especialidad": especialidad,
            "q": q,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
        },
    )


@app.route("/empresa/postulacion/<int:postulacion_id>/estado", methods=["POST"])
@empresa_required
def cambiar_estado_postulacion(postulacion_id):
    empresa = current_empresa()
    postulacion = db.session.get(Postulacion, postulacion_id)
    if not postulacion or postulacion.oferta.empresa_id != empresa.id:
        flash("Postulacion no encontrada.", "error")
        return redirect(url_for("empresa_panel"))

    accion = request.form.get("accion")
    motivo = request.form.get("motivo_empresa", "").strip()

    if postulacion_esta_resuelta(postulacion):
        flash("Esta postulacion ya fue resuelta y no puede aceptarse o rechazarse nuevamente.", "info")
        return redirect(url_for("empresa_panel"))

    if accion == "aceptar":
        if not puede_aceptar_postulacion(postulacion):
            flash("No quedan vacantes disponibles para esta oferta.", "error")
            return redirect(url_for("empresa_panel"))
        postulacion.estado = "Aceptado"
        postulacion.motivo_empresa = motivo or "La empresa acepto tu postulacion."
        ensure_practica(postulacion)
        ensure_mentoria_inicial(postulacion)
    elif accion == "rechazar":
        if not motivo:
            flash("Para rechazar debes indicar el motivo.", "error")
            return redirect(url_for("empresa_panel"))
        postulacion.estado = "Rechazado"
        postulacion.motivo_empresa = motivo
    else:
        flash("Accion no valida.", "error")
        return redirect(url_for("empresa_panel"))

    postulacion.fecha_respuesta = datetime.utcnow()
    add_novedad(
        "postulacion",
        f"Postulacion {postulacion.estado.lower()}",
        f"{empresa.nombre} actualizo la postulacion de {postulacion.usuario.nombre_completo}.",
        usuario=postulacion.usuario,
        empresa=empresa,
        oferta=postulacion.oferta,
    )
    add_notificacion(
        postulacion.usuario,
        "postulacion",
        f"Postulacion {postulacion.estado.lower()}",
        postulacion.motivo_empresa,
        url=url_for("postulado"),
        email=True,
    )
    db.session.commit()
    flash("Estado actualizado.", "success")
    return redirect(url_for("empresa_panel"))


@app.route("/empresa/ofertas/nueva", methods=["GET", "POST"])
@empresa_required
def nueva_oferta():
    empresa = current_empresa()
    if request.method == "POST":
        oferta = Oferta(
            empresa_id=empresa.id,
            titulo=request.form.get("titulo", "").strip(),
            descripcion=request.form.get("descripcion", "").strip(),
            especialidad_req=request.form.get("especialidad_req", "").strip(),
            comuna=request.form.get("comuna", "").strip(),
            modalidad=request.form.get("modalidad", "Presencial"),
            jornada=request.form.get("jornada", "Part-time"),
            tipo=request.form.get("tipo", "Empleo"),
            sueldo=request.form.get("sueldo", "").strip(),
            requisitos=request.form.get("requisitos", "").strip(),
            vacantes=entero_positivo(request.form.get("vacantes"), 1),
            incluye_mentoria=request.form.get("incluye_mentoria") == "1",
            mentor_nombre=request.form.get("mentor_nombre", "").strip(),
            mentor_cargo=request.form.get("mentor_cargo", "").strip(),
            mentor_email=request.form.get("mentor_email", "").strip(),
            mentor_bio=request.form.get("mentor_bio", "").strip(),
            fecha_inicio=request.form.get("fecha_inicio", "").strip(),
            fecha_fin=request.form.get("fecha_fin", "").strip(),
            convenio_digital=request.form.get("convenio_digital", "").strip(),
            horas_practica=entero_positivo(request.form.get("horas_practica"), 450),
        )
        if not all([oferta.titulo, oferta.descripcion, oferta.especialidad_req, oferta.comuna]):
            flash("Completa los datos de la oferta.", "error")
            return redirect(url_for("nueva_oferta"))
        db.session.add(oferta)
        db.session.flush()
        add_novedad("oferta", oferta.titulo, f"{empresa.nombre} publico una nueva oferta.", empresa=empresa, oferta=oferta)
        notificar_oferta_compatible(oferta)
        db.session.commit()
        flash("Oferta publicada.", "success")
        return redirect(url_for("empresa_panel"))
    return render_template("nueva_oferta.html", empresa=empresa)


@app.route("/mentoria")
@login_required
def mentoria():
    postulaciones = (
        Postulacion.query.join(Oferta, Postulacion.oferta_id == Oferta.id)
        .filter(
            Postulacion.usuario_id == current_user.id,
            Postulacion.estado == "Aceptado",
            Oferta.incluye_mentoria.is_(True),
        )
        .order_by(Postulacion.fecha.desc())
        .all()
    )
    return render_template("mentoria.html", postulaciones=postulaciones)


@app.route("/mentoria/sesion/<int:sesion_id>", methods=["POST"])
@login_required
def actualizar_sesion_mentoria(sesion_id):
    sesion = db.session.get(SesionMentoria, sesion_id)
    if not sesion or sesion.postulacion.usuario_id != current_user.id:
        flash("Sesion no encontrada.", "error")
        return redirect(url_for("mentoria"))
    sesion.avances = request.form.get("avances", "").strip()
    sesion.completada = request.form.get("completada") == "1"
    db.session.commit()
    flash("Avance de mentoria actualizado.", "success")
    return redirect(url_for("mentoria"))


@app.route("/empresa/mentoria")
@empresa_required
def empresa_mentoria():
    empresa = current_empresa()
    postulaciones = (
        postulaciones_empresa(empresa)
        .filter(Postulacion.estado == "Aceptado", Oferta.incluye_mentoria.is_(True))
        .order_by(Postulacion.fecha.desc())
        .all()
    )
    return render_template("empresa_mentoria.html", empresa=empresa, postulaciones=postulaciones)


@app.route("/empresa/mentoria/<int:postulacion_id>/sesion", methods=["POST"])
@empresa_required
def crear_sesion_mentoria(postulacion_id):
    empresa = current_empresa()
    postulacion = postulacion_mensajes_autorizada(postulacion_id, empresa)
    if not postulacion or not postulacion.oferta.incluye_mentoria:
        flash("Postulacion no disponible para mentoria.", "error")
        return redirect(url_for("empresa_mentoria"))
    fecha_raw = request.form.get("fecha_programada", "").strip()
    try:
        fecha = datetime.strptime(fecha_raw, "%Y-%m-%dT%H:%M") if fecha_raw else datetime.utcnow()
    except ValueError:
        fecha = datetime.utcnow()
    objetivo = request.form.get("objetivo", "").strip()
    if not objetivo:
        flash("Define un objetivo para la sesion.", "error")
        return redirect(url_for("empresa_mentoria"))
    db.session.add(
        SesionMentoria(
            postulacion_id=postulacion.id,
            fecha_programada=fecha,
            objetivo=objetivo,
        )
    )
    add_notificacion(
        postulacion.usuario,
        "mentoria",
        "Nueva sesion de mentoria",
        f"{empresa.nombre} programo una sesion para {postulacion.oferta.titulo}.",
        url=url_for("mentoria"),
    )
    db.session.commit()
    flash("Sesion programada.", "success")
    return redirect(url_for("empresa_mentoria"))


@app.route("/empresa/mentoria/sesion/<int:sesion_id>/evaluar", methods=["POST"])
@empresa_required
def evaluar_sesion_mentoria(sesion_id):
    empresa = current_empresa()
    sesion = db.session.get(SesionMentoria, sesion_id)
    if not sesion or sesion.postulacion.oferta.empresa_id != empresa.id:
        flash("Sesion no encontrada.", "error")
        return redirect(url_for("empresa_mentoria"))
    sesion.evaluacion = request.form.get("evaluacion", "").strip()
    sesion.completada = request.form.get("completada") == "1"
    db.session.commit()
    flash("Evaluacion guardada.", "success")
    return redirect(url_for("empresa_mentoria"))


@app.route("/practicas")
@login_required
def practicas():
    items = (
        Practica.query.join(Postulacion, Practica.postulacion_id == Postulacion.id)
        .filter(Postulacion.usuario_id == current_user.id)
        .order_by(Practica.fecha_actualizacion.desc())
        .all()
    )
    return render_template("practicas.html", practicas=items)


@app.route("/practicas/<int:practica_id>/seguimiento", methods=["POST"])
@login_required
def registrar_seguimiento_practica(practica_id):
    practica = db.session.get(Practica, practica_id)
    if not practica or practica.postulacion.usuario_id != current_user.id:
        flash("Practica no encontrada.", "error")
        return redirect(url_for("practicas"))
    actividad = request.form.get("actividad", "").strip()
    horas = entero_positivo(request.form.get("horas"), 0, minimo=0)
    if not actividad or horas <= 0:
        flash("Registra actividad y horas validas.", "error")
        return redirect(url_for("practicas"))
    db.session.add(SeguimientoPractica(practica_id=practica.id, horas=horas, actividad=actividad))
    practica.horas_registradas += horas
    practica.fecha_actualizacion = datetime.utcnow()
    db.session.commit()
    flash("Seguimiento registrado.", "success")
    return redirect(url_for("practicas"))


@app.route("/empresa/practicas")
@empresa_required
def empresa_practicas():
    empresa = current_empresa()
    items = (
        Practica.query.join(Postulacion, Practica.postulacion_id == Postulacion.id)
        .join(Oferta, Postulacion.oferta_id == Oferta.id)
        .filter(Oferta.empresa_id == empresa.id)
        .order_by(Practica.fecha_actualizacion.desc())
        .all()
    )
    return render_template("empresa_practicas.html", empresa=empresa, practicas=items)


@app.route("/empresa/practicas/<int:practica_id>/evaluar", methods=["POST"])
@empresa_required
def evaluar_practica_empresa(practica_id):
    empresa = current_empresa()
    practica = db.session.get(Practica, practica_id)
    if not practica or practica.postulacion.oferta.empresa_id != empresa.id:
        flash("Practica no encontrada.", "error")
        return redirect(url_for("empresa_practicas"))
    practica.evaluacion_empresa = request.form.get("evaluacion_empresa", "").strip()
    practica.estado = request.form.get("estado", practica.estado).strip()
    practica.fecha_actualizacion = datetime.utcnow()
    db.session.commit()
    flash("Practica actualizada.", "success")
    return redirect(url_for("empresa_practicas"))


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/admin-nexotp", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password", "") == ADMIN_PASSWORD:
            logout_user()
            session.pop("empresa_id", None)
            session.pop("institucion_id", None)
            session["admin_ok"] = True
            return redirect(url_for("admin_panel"))
        flash("Clave admin incorrecta.", "error")
    return render_template("admin_login.html")


@app.route("/institucion/login", methods=["GET", "POST"])
def institucion_login():
    if request.method == "POST":
        institucion = Institucion.query.filter_by(
            admin_email=request.form.get("email", "").strip().lower()
        ).first()
        if institucion and institucion.check_password(request.form.get("password", "")):
            logout_user()
            session.pop("empresa_id", None)
            session.pop("admin_ok", None)
            session["institucion_id"] = institucion.id
            return redirect(url_for("institucion_panel"))
        flash("Credenciales institucionales incorrectas.", "error")
    return render_template("institucion_login.html")


@app.route("/institucion/panel")
@institucion_required
def institucion_panel():
    institucion = current_institucion()
    usuarios = Usuario.query.order_by(Usuario.fecha_registro.desc()).all()
    empresas = Empresa.query.order_by(Empresa.fecha_registro.desc()).all()
    practicas = Practica.query.order_by(Practica.fecha_actualizacion.desc()).all()
    por_especialidad = []
    for especialidad in ESPECIALIDADES:
        egresados = [u for u in usuarios if u.especialidad == especialidad]
        aceptados_ids = {
            p.usuario_id
            for p in Postulacion.query.join(Oferta, Postulacion.oferta_id == Oferta.id)
            .filter(Oferta.especialidad_req == especialidad, Postulacion.estado == "Aceptado")
            .all()
        }
        tasa = int((len(aceptados_ids) / len(egresados)) * 100) if egresados else 0
        por_especialidad.append({"nombre": especialidad, "egresados": len(egresados), "tasa": tasa})
    metricas = {
        "egresados": len(usuarios),
        "empresas": len(empresas),
        "practicas": len(practicas),
        "aceptados": Postulacion.query.filter_by(estado="Aceptado").count(),
        "ptech": Usuario.query.filter(Usuario.cursos_relevantes.ilike("%PTECH%")).count(),
    }
    return render_template(
        "institucion_panel.html",
        institucion=institucion,
        metricas=metricas,
        por_especialidad=por_especialidad,
        empresas=empresas,
        practicas=practicas,
    )


@app.route("/institucion/practicas/<int:practica_id>/estado", methods=["POST"])
@institucion_required
def actualizar_estado_practica_institucion(practica_id):
    practica = db.session.get(Practica, practica_id)
    if not practica:
        flash("Practica no encontrada.", "error")
        return redirect(url_for("institucion_panel"))
    practica.estado = request.form.get("estado", practica.estado).strip()
    practica.supervisor_liceo = request.form.get("supervisor_liceo", "").strip()
    practica.fecha_actualizacion = datetime.utcnow()
    db.session.commit()
    flash("Seguimiento institucional actualizado.", "success")
    return redirect(url_for("institucion_panel"))


@app.route("/institucion/reporte.csv")
@institucion_required
def reporte_institucion_csv():
    salida = StringIO()
    writer = csv.writer(salida)
    writer.writerow(["Especialidad", "Egresados", "Tasa insercion", "Practicas", "Empresas aliadas"])
    empresas_total = Empresa.query.count()
    for especialidad in ESPECIALIDADES:
        egresados = Usuario.query.filter_by(especialidad=especialidad).count()
        aceptados = (
            Postulacion.query.join(Oferta, Postulacion.oferta_id == Oferta.id)
            .filter(Oferta.especialidad_req == especialidad, Postulacion.estado == "Aceptado")
            .count()
        )
        practicas_total = (
            Practica.query.join(Postulacion, Practica.postulacion_id == Postulacion.id)
            .join(Oferta, Postulacion.oferta_id == Oferta.id)
            .filter(Oferta.especialidad_req == especialidad)
            .count()
        )
        tasa = int((aceptados / egresados) * 100) if egresados else 0
        writer.writerow([especialidad, egresados, f"{tasa}%", practicas_total, empresas_total])
    return Response(
        salida.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=reporte-impacto-nexotp.csv"},
    )


@app.route("/admin-nexotp/panel")
@admin_required
def admin_panel():
    return render_template(
        "admin_panel.html",
        usuarios=Usuario.query.order_by(Usuario.fecha_registro.desc()).all(),
        empresas=Empresa.query.order_by(Empresa.fecha_registro.desc()).all(),
        ofertas=Oferta.query.order_by(Oferta.fecha_publicacion.desc()).all(),
        postulaciones=Postulacion.query.order_by(Postulacion.fecha.desc()).all(),
        novedades=Novedad.query.order_by(Novedad.fecha.desc()).limit(30).all(),
    )


@app.route("/admin-nexotp/usuario/<int:usuario_id>/editar", methods=["GET", "POST"])
@admin_required
def admin_editar_usuario(usuario_id):
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("admin_panel"))
    if request.method == "POST":
        for field in [
            "nombre",
            "apellido",
            "email",
            "telefono",
            "comuna",
            "pais",
            "especialidad",
            "perfil_profesional",
            "habilidades_tecnicas",
            "habilidades_blandas",
            "idiomas",
            "herramientas",
            "certificaciones",
            "experiencia_laboral",
            "proyectos",
            "referencias",
            "linkedin",
            "portafolio",
        ]:
            setattr(usuario, field, request.form.get(field, "").strip())
        password = request.form.get("password", "").strip()
        if password:
            usuario.set_password(password)
        try:
            db.session.commit()
            flash("Usuario actualizado.", "success")
            return redirect(url_for("admin_panel"))
        except IntegrityError:
            db.session.rollback()
            flash("No se pudo guardar. Revisa que el correo no este duplicado.", "error")
    return render_template("admin_edit_usuario.html", usuario=usuario)


@app.route("/admin-nexotp/empresa/<int:empresa_id>/editar", methods=["GET", "POST"])
@admin_required
def admin_editar_empresa(empresa_id):
    empresa = db.session.get(Empresa, empresa_id)
    if not empresa:
        flash("Empresa no encontrada.", "error")
        return redirect(url_for("admin_panel"))
    if request.method == "POST":
        for field in ["nombre", "email", "rubro", "descripcion", "ubicacion", "contacto", "web", "foto_url", "logo_inicial", "color"]:
            setattr(empresa, field, request.form.get(field, "").strip())
        empresa.amigable_tp = request.form.get("amigable_tp") == "1"
        password = request.form.get("password", "").strip()
        if password:
            empresa.set_password(password)
        try:
            db.session.commit()
            flash("Empresa actualizada.", "success")
            return redirect(url_for("admin_panel"))
        except IntegrityError:
            db.session.rollback()
            flash("No se pudo guardar. Revisa que el correo no este duplicado.", "error")
    return render_template("admin_edit_empresa.html", empresa=empresa)


@app.route("/admin-nexotp/oferta/<int:oferta_id>/editar", methods=["GET", "POST"])
@admin_required
def admin_editar_oferta(oferta_id):
    oferta = db.session.get(Oferta, oferta_id)
    if not oferta:
        flash("Oferta no encontrada.", "error")
        return redirect(url_for("admin_panel"))
    if request.method == "POST":
        for field in [
            "titulo",
            "descripcion",
            "especialidad_req",
            "comuna",
            "modalidad",
            "jornada",
            "tipo",
            "sueldo",
            "requisitos",
            "mentor_nombre",
            "mentor_cargo",
            "mentor_email",
            "mentor_bio",
            "fecha_inicio",
            "fecha_fin",
            "convenio_digital",
        ]:
            if field in request.form:
                setattr(oferta, field, request.form.get(field, "").strip())
        nuevas_vacantes = entero_positivo(request.form.get("vacantes"), 1)
        aceptados_actuales = aceptados_oferta(oferta)
        if nuevas_vacantes < aceptados_actuales:
            flash(
                f"No puedes dejar menos vacantes ({nuevas_vacantes}) que postulantes aceptados ({aceptados_actuales}).",
                "error",
            )
            return redirect(url_for("admin_editar_oferta", oferta_id=oferta.id))
        oferta.vacantes = nuevas_vacantes
        oferta.horas_practica = entero_positivo(request.form.get("horas_practica"), 450)
        oferta.incluye_mentoria = request.form.get("incluye_mentoria") == "1"
        oferta.activa = request.form.get("activa") == "1"
        db.session.commit()
        flash("Oferta actualizada.", "success")
        return redirect(url_for("admin_panel"))
    return render_template("admin_edit_oferta.html", oferta=oferta)


@app.route("/admin-nexotp/postulacion/<int:postulacion_id>/editar", methods=["GET", "POST"])
@admin_required
def admin_editar_postulacion(postulacion_id):
    postulacion = db.session.get(Postulacion, postulacion_id)
    if not postulacion:
        flash("Postulacion no encontrada.", "error")
        return redirect(url_for("admin_panel"))
    if request.method == "POST":
        estado_anterior = postulacion.estado
        nuevo_estado = request.form.get("estado", "En revision").strip()
        if nuevo_estado == "Aceptado" and estado_anterior != "Aceptado" and not puede_aceptar_postulacion(postulacion):
            flash("No quedan vacantes disponibles para aceptar esta postulacion.", "error")
            return redirect(url_for("admin_editar_postulacion", postulacion_id=postulacion.id))
        postulacion.estado = nuevo_estado
        postulacion.mensaje = request.form.get("mensaje", "").strip()
        postulacion.motivo_empresa = request.form.get("motivo_empresa", "").strip()
        if postulacion.estado in {"Aceptado", "Rechazado"} and not postulacion.fecha_respuesta:
            postulacion.fecha_respuesta = datetime.utcnow()
        if postulacion.estado == "Aceptado" and estado_anterior != "Aceptado":
            ensure_practica(postulacion)
            ensure_mentoria_inicial(postulacion)
        db.session.commit()
        flash("Postulacion actualizada.", "success")
        return redirect(url_for("admin_panel"))
    return render_template("admin_edit_postulacion.html", postulacion=postulacion)


@app.route("/admin-nexotp/eliminar/<tipo>/<int:item_id>", methods=["POST"])
@admin_required
def admin_eliminar(tipo, item_id):
    modelos = {
        "usuario": Usuario,
        "empresa": Empresa,
        "oferta": Oferta,
        "postulacion": Postulacion,
        "conexion": Conexion,
        "novedad": Novedad,
        "notificacion": Notificacion,
        "mensaje": Mensaje,
        "sesion_mentoria": SesionMentoria,
        "resena": ResenaEmpresa,
        "institucion": Institucion,
        "practica": Practica,
        "seguimiento_practica": SeguimientoPractica,
    }
    modelo = modelos.get(tipo)
    if not modelo:
        flash("Tipo no valido.", "error")
        return redirect(url_for("admin_panel"))
    item = db.session.get(modelo, item_id)
    if not item:
        flash("Registro no encontrado.", "error")
        return redirect(url_for("admin_panel"))
    db.session.delete(item)
    db.session.commit()
    flash("Registro eliminado.", "success")
    return redirect(url_for("admin_panel"))


@app.route("/design-thinking")
def design_thinking():
    return render_template("design_thinking.html")


@app.route("/mapa")
@login_required
def mapa():
    comuna = request.args.get("comuna", "").strip()
    especialidad = request.args.get("especialidad", "").strip()
    radio = request.args.get("radio", "10").strip()
    try:
        radio_km = max(1, float(radio))
    except ValueError:
        radio_km = 10
    query = Oferta.query.filter_by(activa=True)
    if comuna:
        query = query.filter_by(comuna=comuna)
    if especialidad:
        query = query.filter_by(especialidad_req=especialidad)
    ofertas = query.order_by(Oferta.fecha_publicacion.desc()).all()
    centro_coords = COMUNA_COORDS.get(current_user.comuna, COMUNA_COORDS["Santiago"])
    if not comuna:
        ofertas = [
            oferta for oferta in ofertas
            if distancia_km(centro_coords, COMUNA_COORDS.get(oferta.comuna, COMUNA_COORDS["Santiago"])) <= radio_km
        ]
    puntos = []
    for oferta in ofertas:
        lat, lng = COMUNA_COORDS.get(oferta.comuna, COMUNA_COORDS["Santiago"])
        puntos.append(
            {
                "titulo": oferta.titulo,
                "empresa": oferta.empresa.nombre,
                "comuna": oferta.comuna,
                "especialidad": oferta.especialidad_req,
                "tipo": oferta.tipo,
                "match": calcular_match(current_user, oferta),
                "lat": lat,
                "lng": lng,
            }
        )
    densidad = []
    for comuna_nombre in COMUNAS:
        total = sum(1 for oferta in ofertas if oferta.comuna == comuna_nombre)
        if total:
            lat, lng = COMUNA_COORDS.get(comuna_nombre, COMUNA_COORDS["Santiago"])
            densidad.append({"comuna": comuna_nombre, "total": total, "lat": lat, "lng": lng})
    return render_template(
        "mapa.html",
        puntos=json.dumps(puntos),
        densidad=json.dumps(densidad),
        filtros={"comuna": comuna, "especialidad": especialidad, "radio": int(radio_km)},
        centro=json.dumps(centro_coords),
        radio=int(radio_km),
    )


@app.route("/api/stats")
def api_stats():
    return jsonify(
        {
            "usuarios": Usuario.query.count(),
            "empresas": Empresa.query.count(),
            "ofertas": Oferta.query.filter_by(activa=True).count(),
            "postulaciones": Postulacion.query.count(),
            "conexiones": Conexion.query.count(),
            "novedades": Novedad.query.count(),
            "notificaciones": Notificacion.query.count(),
            "mensajes": Mensaje.query.count(),
            "practicas": Practica.query.count(),
            "instituciones": Institucion.query.count(),
        }
    )


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


with app.app_context():
    init_database()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=os.environ.get("FLASK_DEBUG") == "1",
        use_reloader=False,
        threaded=True,
    )