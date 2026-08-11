# NexoTP

Plataforma para conectar egresados tecnico-profesionales con empresas,
practicas, mentorias y seguimiento institucional.

## Arquitectura

```text
apps/
  frontend/                 React 19 + Vite + Bootstrap
    src/
    public/
  backend/                  FastAPI + Flask/SQLAlchemy
    app/
      core/                 configuracion y seguridad
      static/
      templates/
      legacy.py             reglas de negocio existentes
      main.py               entrada ASGI
deployment/                 Docker, Nginx y Compose
docs/
```

FastAPI es el punto de entrada del backend. Durante la migracion incremental,
las reglas de negocio existentes se ejecutan mediante un adaptador WSGI. El
frontend React consume esas rutas por HTTP. La siguiente etapa recomendada es
extraer cada dominio de `legacy.py` a endpoints JSON versionados.

## Variables de entorno

Copia los ejemplos de `apps/backend/.env.example` y
`deployment/.env.example`. No confirmes nunca archivos `.env`.

En produccion son obligatorias:

- `APP_ENV=production`
- `SECRET_KEY` de al menos 32 caracteres aleatorios
- `ADMIN_PASSWORD_HASH`, nunca la contrasena administrativa en texto plano
- `DATABASE_URL` de PostgreSQL
- `ALLOWED_ORIGINS` limitado al dominio publico

El servidor se niega a iniciar en produccion si faltan los secretos
principales.

Genera el hash administrativo y guarda solamente el resultado en el
administrador de secretos del proveedor:

```powershell
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash(input('Password: ')))"
```

## Verificacion

```powershell
Set-Location apps/frontend
npm run lint
npm run build
```

```powershell
Set-Location ../..
python -m pytest
```

## Despliegue

```powershell
Copy-Item deployment/.env.example deployment/.env
# Reemplaza todos los valores de ejemplo antes de continuar.
docker compose --env-file deployment/.env -f deployment/docker-compose.yml up --build
```

El servicio publico escucha en el puerto `8080` y debe publicarse detras del
HTTPS administrado por el proveedor o de un proxy TLS.

Consulta [SECURITY.md](SECURITY.md) antes de publicar y
[docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md) para las consideraciones del
proveedor.

La guia completa para publicar sin costo esta en
[docs/DESPLIEGUE_GRATUITO.md](docs/DESPLIEGUE_GRATUITO.md).
