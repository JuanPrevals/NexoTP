# Deploy en Render

Guia para publicar NexoTP como servicio web Flask en Render.

## 1. Preparar GitHub

El repositorio remoto actual apunta a:

```text
https://github.com/JuanPrevals/NexoTP.git
```

Flujo normal:

```bash
git status
git add .
git commit -m "Describe el cambio"
git push origin main
```

## 2. Crear Web Service

1. Entrar a Render.
2. New > Web Service.
3. Conectar el repositorio de GitHub.
4. Runtime: Python.
5. Branch: `main`.
6. Build Command:

```bash
pip install -r requirements.txt
```

7. Start Command:

```bash
gunicorn app:app
```

El `Procfile` ya contiene:

```text
web: gunicorn app:app
```

## 3. Variables de entorno

Configura al menos:

| Variable | Recomendacion |
|---|---|
| `SECRET_KEY` | Valor largo y privado. |
| `ADMIN_PASSWORD` | Password seguro para `/admin-nexotp`. |
| `FLASK_DEBUG` | `0` en produccion. |

Opcionales para correos reales:

| Variable | Uso |
|---|---|
| `SMTP_HOST` | Host SMTP. |
| `SMTP_PORT` | Puerto, normalmente `587`. |
| `SMTP_USER` | Usuario SMTP. |
| `SMTP_PASSWORD` | Password SMTP. |
| `MAIL_FROM` | Remitente visible. |

Si SMTP no esta configurado, las notificaciones siguen disponibles dentro de la app y en tiempo real.

## 4. Base de datos

La app usa SQLite por defecto:

```python
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///nexotp.db"
```

Esto sirve para demo y desarrollo local, pero no es ideal para produccion. Render puede reiniciar instancias y el filesystem no debe tratarse como base persistente confiable.

Para produccion se recomienda mover a Postgres administrado, por ejemplo Render Postgres, Neon o Supabase.

Patron sugerido para adaptar `app.py`:

```python
db_url = os.environ.get("DATABASE_URL", "sqlite:///nexotp.db")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
```

Luego configurar `DATABASE_URL` en Render.

## 5. Realtime y Gunicorn

NexoTP usa Server-Sent Events para notificaciones, mensajes y estado de escritura.

Para demo simple, `gunicorn app:app` funciona. Si hay muchos usuarios concurrentes, conviene evaluar workers/threads:

```bash
gunicorn --workers 2 --threads 4 app:app
```

Evita usar configuraciones que corten conexiones largas demasiado pronto, porque SSE mantiene una conexion abierta por usuario.

## 6. Validacion post deploy

Probar estas rutas:

- `/`
- `/login`
- `/feed`
- `/mensajes`
- `/notificaciones`
- `/empresa/login`
- `/empresa/panel`
- `/institucion/login`
- `/institucion/panel`
- `/admin-nexotp`

Credenciales demo:

| Rol | Email | Password |
|---|---|---|
| Egresado | `demo@nexotp.cl` | `demo123` |
| Empresa | `empresa@nexotp.cl` | `empresa123` |
| Liceo | `liceo@nexotp.cl` | `liceo123` |
| Admin | - | Valor de `ADMIN_PASSWORD` |

## 7. Checklist funcional

- Crear perfil nuevo y confirmar que aparece la guia inicial.
- Postular a una oferta.
- Entrar como empresa y resolver la postulacion.
- Verificar que una postulacion ya resuelta no se pueda aceptar de nuevo.
- Probar mensajes en una postulacion no rechazada.
- Probar que una postulacion rechazada deja el chat como historial.
- Abrir campana de notificaciones y marcar como leido.
- Generar CV PDF desde `/perfil`.
- Revisar mapa de oportunidades.
- Exportar reporte CSV institucional.

## 8. Notas de produccion

- Cambiar `SECRET_KEY` y `ADMIN_PASSWORD`.
- Usar HTTPS.
- Usar Postgres para persistencia.
- Configurar backups.
- Revisar politicas de privacidad si se usara con datos reales.
- No usar credenciales demo en produccion.
