# Despliegue seguro

La arquitectura contiene dos servicios:

- Backend ASGI: `apps.backend.app.main:app`.
- Frontend estatico: resultado de `npm run build` en `apps/frontend/dist`.

## Backend

Configura el directorio raiz del servicio en la raiz del repositorio.

- Build: `pip install -r apps/backend/requirements.txt`
- Start: `uvicorn apps.backend.app.main:app --host 0.0.0.0 --port $PORT --proxy-headers`
- Health check: `/api/health`

Variables obligatorias:

```text
APP_ENV=production
DATABASE_URL=postgresql+psycopg://...
SECRET_KEY=<valor aleatorio de 32 o mas caracteres>
ADMIN_PASSWORD_HASH=<hash generado por Werkzeug>
ADMIN_PATH=<ruta-administrativa-privada-sin-barras>
ALLOWED_ORIGINS=https://tu-dominio.example
```

Si `ADMIN_PATH=control-nexo-8f4d2a91`, el formulario de acceso queda en
`/control-nexo-8f4d2a91` y el panel en `/control-nexo-8f4d2a91/panel`. El valor
admite entre 8 y 80 letras, numeros, guiones o guiones bajos. Cambiarlo requiere
reiniciar el servicio y hace que la ruta anterior responda 404.

No uses SQLite en un filesystem efimero. Crea una base PostgreSQL administrada,
habilita respaldos y usa una cuenta con privilegios limitados.

## Frontend

- Root: `apps/frontend`
- Build: `npm ci && npm run build`
- Publish directory: `dist`

El proxy debe dirigir `/backend-page/*` y `/api/*` al backend. Si el proveedor
no permite reescrituras, usa los contenedores de `deployment/`, cuyo Nginx ya
incluye esa configuracion.

## Dominio y HTTPS

Expone un solo dominio publico, fuerza HTTPS y no publiques directamente el
puerto de Uvicorn. Revisa las cabeceras, cookies seguras y CORS después de
conectar el dominio definitivo.

## Antes de publicar

```powershell
python -m pytest -q
Set-Location apps/frontend
npm ci
npm run lint
npm run build
```

Consulta tambien `SECURITY.md`.
