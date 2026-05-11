# NexoTP

NexoTP es una plataforma web en Flask para conectar egresados tecnico-profesionales con empresas, practicas, mentorias y seguimiento institucional. El proyecto esta orientado al primer empleo TP, especialmente para estudiantes que necesitan mostrar competencias, construir CV/portafolio, conversar con empleadores y encontrar oportunidades cercanas.

## Funcionalidades principales

### Egresados
- Registro e inicio de sesion.
- Feed de ofertas ordenado por compatibilidad.
- Matching inteligente segun habilidades, especialidad y comuna.
- Dashboard personal con postulaciones, respuestas, tasa de aceptacion y recomendaciones.
- Perfil editable y perfil publico.
- Generador de CV en PDF con enlace al perfil publico.
- Postulaciones con seguimiento de estado.
- Mensajeria en tiempo real con empresas.
- Indicador de "esta escribiendo" en conversaciones.
- Campana de notificaciones en tiempo real.
- Mapa de oportunidades por comuna y radio de busqueda.
- Modulo de practicas profesionales con registro de horas.
- Modulo de mentoria con sesiones, objetivos, avances y evaluaciones.
- Guia inicial saltable para usuarios nuevos.

### Empresas
- Registro e inicio de sesion para empresas.
- Publicacion de ofertas de empleo o practica.
- Gestion de postulaciones desde panel de empresa.
- Seguridad por empresa: cada empresa solo gestiona sus propias ofertas/postulaciones.
- Filtros de postulaciones por estado, oferta, modalidad, jornada, especialidad, texto y fechas.
- Control de vacantes: no se puede aceptar mas postulantes que cupos disponibles.
- Prevencion de dobles resoluciones: una postulacion aceptada o rechazada queda cerrada.
- Mensajeria con postulantes, cerrada automaticamente si la postulacion fue rechazada.
- Gestion de mentorias y practicas.
- Perfil publico de empresa con resenas, ofertas activas y estadisticas.

### Liceo / institucion
- Acceso institucional.
- Panel de impacto para seguimiento del programa.
- Metricas por especialidad, egresados, empresas aliadas, practicas y aceptaciones.
- Supervision de practicas.
- Exportacion CSV de reporte institucional.

### Administracion
- Panel admin global.
- Edicion de usuarios, empresas, ofertas y postulaciones.
- Eliminacion de registros.
- Validaciones para mantener consistencia de vacantes y postulaciones.

## Credenciales demo

| Rol | Email | Password | Ruta |
|---|---|---|---|
| Egresado | `demo@nexotp.cl` | `demo123` | `/login` |
| Empresa | `empresa@nexotp.cl` | `empresa123` | `/empresa/login` |
| Liceo | `liceo@nexotp.cl` | `liceo123` | `/institucion/login` |
| Admin | - | `admin123` por defecto | `/admin-nexotp` |

Configura `ADMIN_PASSWORD` en produccion.

## Stack tecnico

- Python 3.x
- Flask
- Flask-SQLAlchemy
- Flask-Login
- SQLite local
- ReportLab para PDF
- Server-Sent Events para actualizaciones en tiempo real
- Leaflet.js para mapa interactivo
- Gunicorn para deploy

## Estructura

```text
NexoTP/
  app.py
  requirements.txt
  Procfile
  README.md
  10_mejoras_nexotp.md
  templates/
  static/
    css/
    js/
  docs/
  screenshots/
```

## Ejecucion local

```bash
python -m pip install -r requirements.txt
python app.py
```

Abrir:

```text
http://127.0.0.1:5000
```

En PowerShell:

```powershell
$env:SECRET_KEY="cambia-esto"
$env:ADMIN_PASSWORD="cambia-esto"
python app.py
```

## Variables de entorno

| Variable | Uso |
|---|---|
| `SECRET_KEY` | Clave de sesion Flask. |
| `ADMIN_PASSWORD` | Password del panel admin. |
| `FLASK_DEBUG` | Usar `1` para debug local. |
| `SMTP_HOST` | Host SMTP para correos reales. |
| `SMTP_PORT` | Puerto SMTP, por defecto `587`. |
| `SMTP_USER` | Usuario SMTP. |
| `SMTP_PASSWORD` | Password SMTP. |
| `MAIL_FROM` | Remitente de correos. |

Si no configuras SMTP, las notificaciones siguen funcionando dentro de la plataforma.

## Rutas importantes

### Publicas
- `/`
- `/faq`
- `/login`
- `/registro`
- `/empresa/login`
- `/empresa/registro`
- `/institucion/login`
- `/design-thinking`

### Egresado
- `/feed`
- `/dashboard`
- `/postulado`
- `/mensajes`
- `/notificaciones`
- `/perfil`
- `/perfil/editar`
- `/perfil/cv.pdf`
- `/practicas`
- `/mentoria`
- `/mapa`
- `/empresas`
- `/u/<usuario_id>`

### Empresa
- `/empresa/panel`
- `/empresa/ofertas/nueva`
- `/empresa/mensajes`
- `/empresa/mentoria`
- `/empresa/practicas`
- `/empresa/<empresa_id>`

### Institucion y admin
- `/institucion/panel`
- `/institucion/reporte.csv`
- `/admin-nexotp`
- `/admin-nexotp/panel`

## Flujo funcional recomendado

1. El egresado crea su perfil y recibe una guia inicial saltable.
2. Completa habilidades, experiencia, proyectos y datos de contacto.
3. Revisa el feed, usa filtros o mapa y postula a ofertas.
4. La empresa revisa postulaciones desde su panel.
5. La empresa acepta o rechaza, respetando vacantes y evitando acciones duplicadas.
6. Si la postulacion sigue activa, empresa y egresado pueden conversar.
7. Si la oferta incluye practica o mentoria, se habilitan sus modulos de seguimiento.
8. El liceo revisa impacto, practicas y reportes desde el panel institucional.

## Reglas de negocio implementadas

- No se puede postular dos veces a la misma oferta.
- Una postulacion aceptada o rechazada queda resuelta y no puede resolverse otra vez desde empresa.
- Si una postulacion fue rechazada, la conversacion queda como historial y no permite nuevos mensajes.
- No se puede aceptar mas postulantes que vacantes disponibles.
- Admin no puede reducir vacantes por debajo de postulantes ya aceptados.
- Las notificaciones marcadas como leidas se eliminan de la lista.
- La campana no muestra circulo ni contador cuando no hay notificaciones.

## Tiempo real

La app usa Server-Sent Events en `/api/realtime/stream` para:

- Actualizar notificaciones.
- Actualizar conversaciones.
- Mostrar indicador de escritura.

Tambien existe un respaldo ligero desde frontend para refrescar la conversacion activa si el stream del navegador se retrasa.

## Base de datos

En local se usa SQLite. La app crea y actualiza tablas al iniciar mediante `db.create_all()` y migraciones aditivas simples para columnas nuevas.

Para produccion se recomienda Postgres. Ver [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md).

## Deploy

El proyecto incluye `Procfile`:

```text
web: gunicorn app:app
```

Guia de deploy:

[docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md)

## Documentos del proyecto

- [10_mejoras_nexotp.md](10_mejoras_nexotp.md): lista de mejoras usadas como referencia funcional.
- [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md): guia de deploy.
- [docs/CHANGELOG.md](docs/CHANGELOG.md): resumen de cambios principales.
- [screenshots/home-referencial.svg](screenshots/home-referencial.svg): captura referencial.

## Estado actual

- Repo local y remoto configurado.
- Rama principal: `main`.
- Ultimo objetivo implementado: mejoras integrales de NexoTP, mensajeria realtime, notificaciones, feed responsive, FAQ ampliado y guia inicial para usuarios nuevos.

## Licencia

Uso academico / proyecto demostrativo.
