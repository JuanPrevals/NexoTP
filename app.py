from datetime import datetime
import os

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
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
from sqlalchemy import inspect, or_
from sqlalchemy.exc import IntegrityError, OperationalError
from werkzeug.security import check_password_hash, generate_password_hash


APP_NAME = "NexoTP"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "nexotp-dev")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///nexotp.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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
    logo_inicial = db.Column(db.String(5))
    color = db.Column(db.String(20), default="#1f2937")
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
    sueldo = db.Column(db.String(80))
    vacantes = db.Column(db.Integer, default=1)
    requiere_experiencia = db.Column(db.Boolean, default=False)
    incluye_mentoria = db.Column(db.Boolean, default=True)
    requisitos = db.Column(db.Text)
    fecha_publicacion = db.Column(db.DateTime, default=datetime.utcnow)
    activa = db.Column(db.Boolean, default=True)

    postulaciones = db.relationship(
        "Postulacion", backref="oferta", cascade="all, delete-orphan", lazy=True
    )

    @property
    def requisitos_lista(self):
        return [r.strip() for r in (self.requisitos or "").split(";") if r.strip()]


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


def current_empresa():
    empresa_id = session.get("empresa_id")
    if not empresa_id:
        return None
    return db.session.get(Empresa, empresa_id)


def empresa_required(view):
    def wrapper(*args, **kwargs):
        if not current_empresa():
            flash("Ingresa como empresa.", "info")
            return redirect(url_for("empresa_login"))
        return view(*args, **kwargs)

    wrapper.__name__ = view.__name__
    return wrapper


def admin_required(view):
    def wrapper(*args, **kwargs):
        if not session.get("admin_ok"):
            flash("Acceso admin requerido.", "info")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    wrapper.__name__ = view.__name__
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


def seed_data():
    if Empresa.query.count() > 0:
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
            oferta = Oferta(
                empresa_id=empresa.id,
                titulo=titulo,
                descripcion=desc,
                especialidad_req=esp,
                comuna=comuna,
                modalidad=mod,
                jornada=jornada,
                sueldo=sueldo,
                requisitos=req,
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
    db.session.commit()


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
        if schema_needs_rebuild():
            db.drop_all()
        db.create_all()
        seed_data()
    except OperationalError:
        db.session.rollback()
        db.drop_all()
        db.create_all()
        seed_data()


@app.context_processor
def inject_globals():
    return {
        "app_name": APP_NAME,
        "especialidades": ESPECIALIDADES,
        "comunas": COMUNAS,
        "modalidades": MODALIDADES,
        "jornadas": JORNADAS,
        "empresa_actual": current_empresa(),
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
    ofertas = query.order_by(Oferta.fecha_publicacion.desc()).all()
    novedades = Novedad.query.order_by(Novedad.fecha.desc()).limit(12)
    return render_template(
        "feed.html",
        ofertas=ofertas,
        mis_postulaciones=mis_postulaciones,
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
    postulacion = Postulacion(usuario_id=current_user.id, oferta_id=oferta.id)
    db.session.add(postulacion)
    add_novedad("postulacion", "Nueva postulacion", f"{current_user.nombre_completo} postulo a {oferta.titulo}.", usuario=current_user, empresa=oferta.empresa, oferta=oferta)
    db.session.commit()
    return jsonify({"ok": True, "message": "Postulacion enviada."})


@app.route("/perfil")
@login_required
def perfil():
    postulaciones = Postulacion.query.filter_by(usuario_id=current_user.id).order_by(Postulacion.fecha.desc()).all()
    conexiones = Conexion.query.filter_by(usuario_id=current_user.id).all()
    return render_template("perfil.html", postulaciones=postulaciones, conexiones=conexiones)


@app.route("/postulado")
@login_required
def postulado():
    postulaciones = Postulacion.query.filter_by(usuario_id=current_user.id).order_by(Postulacion.fecha.desc()).all()
    return render_template("postulado.html", postulaciones=postulaciones)


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


@app.route("/empresa/login", methods=["GET", "POST"])
def empresa_login():
    if request.method == "POST":
        empresa = Empresa.query.filter_by(email=request.form.get("email", "").strip().lower()).first()
        if empresa and empresa.check_password(request.form.get("password", "")):
            logout_user()
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

    return render_template(
        "empresa_panel.html",
        empresa=empresa,
        ofertas=ofertas,
        postulaciones=postulaciones,
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
    if accion == "aceptar":
        postulacion.estado = "Aceptado"
        postulacion.motivo_empresa = motivo or "La empresa acepto tu postulacion."
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
            sueldo=request.form.get("sueldo", "").strip(),
            requisitos=request.form.get("requisitos", "").strip(),
            vacantes=int(request.form.get("vacantes") or 1),
        )
        if not all([oferta.titulo, oferta.descripcion, oferta.especialidad_req, oferta.comuna]):
            flash("Completa los datos de la oferta.", "error")
            return redirect(url_for("nueva_oferta"))
        db.session.add(oferta)
        db.session.flush()
        add_novedad("oferta", oferta.titulo, f"{empresa.nombre} publico una nueva oferta.", empresa=empresa, oferta=oferta)
        db.session.commit()
        flash("Oferta publicada.", "success")
        return redirect(url_for("empresa_panel"))
    return render_template("nueva_oferta.html", empresa=empresa)


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/admin-nexotp", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password", "") == ADMIN_PASSWORD:
            logout_user()
            session.pop("empresa_id", None)
            session["admin_ok"] = True
            return redirect(url_for("admin_panel"))
        flash("Clave admin incorrecta.", "error")
    return render_template("admin_login.html")


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
        for field in ["nombre", "email", "rubro", "descripcion", "ubicacion", "contacto", "web", "logo_inicial", "color"]:
            setattr(empresa, field, request.form.get(field, "").strip())
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
        for field in ["titulo", "descripcion", "especialidad_req", "comuna", "modalidad", "jornada", "sueldo", "requisitos"]:
            setattr(oferta, field, request.form.get(field, "").strip())
        oferta.vacantes = int(request.form.get("vacantes") or 1)
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
        postulacion.estado = request.form.get("estado", "En revision").strip()
        postulacion.mensaje = request.form.get("mensaje", "").strip()
        postulacion.motivo_empresa = request.form.get("motivo_empresa", "").strip()
        if postulacion.estado in {"Aceptado", "Rechazado"} and not postulacion.fecha_respuesta:
            postulacion.fecha_respuesta = datetime.utcnow()
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
        }
    )


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    with app.app_context():
        init_database()
    app.run(host="0.0.0.0", port=5000, debug=os.environ.get("FLASK_DEBUG") == "1", use_reloader=False)
