# Publicar NexoTP gratis, paso a paso

Esta guia explica como publicar NexoTP en Internet usando servicios con planes
gratuitos y una arquitectura persistente basada en PostgreSQL.

> Los planes gratuitos pueden cambiar. Render suspende los servicios inactivos
> y el primer acceso puede tardar. No se debe prometer disponibilidad comercial
> usando infraestructura gratuita.

## Arquitectura elegida

Para la primera publicacion usaremos:

```text
GitHub                  codigo y despliegues
Render Web Service      backend FastAPI/Python
Render Static Site      frontend React compilado
Neon                    base de datos PostgreSQL
```

Las direcciones gratuitas se pareceran a estas:

```text
Frontend: https://nexotp.onrender.com
Backend:  https://nexotp-api.onrender.com
```

La base de datos no es publica para los visitantes. Solo el backend conoce su
cadena de conexion.

## 1. Requisitos y cuentas

Crea cuentas gratuitas en:

1. GitHub: <https://github.com/>
2. Neon: <https://neon.com/>
3. Render: <https://render.com/>

Conviene entrar a Neon y Render usando la misma cuenta de GitHub.

En el computador comprueba:

```powershell
git --version
python --version
node --version
npm --version
```

## 2. Revisar que no se publiquen secretos

Desde la raiz de NexoTP ejecuta:

```powershell
git status --short
git check-ignore apps/backend/instance/nexotp.db
git check-ignore apps/frontend/node_modules
git check-ignore .env
```

Los tres ultimos comandos deben mostrar que los elementos estan ignorados.

Nunca confirmes en Git:

```text
.env
*.db
node_modules/
dist/
claves privadas
tokens
contrasenas
cadenas DATABASE_URL
```

Si un secreto fue publicado alguna vez, borrarlo del archivo no es suficiente:
hay que revocarlo o cambiarlo.

## 3. Verificar la version que se publicara

Instala y prueba el backend:

```powershell
python -m pip install -r apps/backend/requirements-dev.txt
python -m pytest -q
```

Prueba el frontend:

```powershell
Set-Location apps/frontend
npm ci
npm run lint
npm run build
Set-Location ../..
```

Antes de publicar, todas las pruebas y la compilacion deben terminar sin
errores.

## 4. Subir el codigo a GitHub

Comprueba el repositorio remoto:

```powershell
git remote -v
```

Si todavia no existe un remoto, crea un repositorio vacio en GitHub y enlazalo:

```powershell
git remote add origin https://github.com/TU-USUARIO/NexoTP.git
git branch -M main
```

Revisa los archivos y publica:

```powershell
git status
git add .
git status
git commit -m "Prepara NexoTP para despliegue"
git push -u origin main
```

Lee una vez mas la lista de `git status` antes de confirmar. No uses `git add .`
si aparece un secreto o una base de datos.

## 5. Crear PostgreSQL gratis en Neon

1. Entra a Neon.
2. Selecciona **New project**.
3. Usa `nexotp` como nombre.
4. Selecciona una region cercana cuando sea posible.
5. Conserva PostgreSQL como tipo de base.
6. Abre **Connection details**.
7. Selecciona una conexion con pooling si Neon la ofrece.
8. Copia la cadena de conexion.

Neon entrega algo parecido a:

```text
postgresql://usuario:password@host.neon.tech/neondb?sslmode=require
```

Para SQLAlchemy se usara:

```text
postgresql+psycopg://usuario:password@host.neon.tech/neondb?sslmode=require
```

Solo cambia el prefijo `postgresql://` por `postgresql+psycopg://`. No alteres
el resto.

Guarda esta cadena temporalmente en un administrador de contrasenas. No la
escribas en un archivo del repositorio.

### Preparar la base de produccion

Para el primer despliegue se recomienda comenzar con la base Neon vacia.
NexoTP crea su esquema y datos iniciales al arrancar.

Si necesitas conservar usuarios o postulaciones existentes, realiza una
migracion controlada a PostgreSQL antes de abrir el sitio al publico.

## 6. Generar secretos de produccion

Genera una clave de sesion:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Guarda el resultado como `SECRET_KEY`.

Genera el hash de la contraseña administrativa:

```powershell
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash(input('Password administrador: ')))"
```

Escribe una contraseña larga y unica. Guarda como `ADMIN_PASSWORD_HASH`
solamente la cadena generada; nunca guardes la contraseña original en Render o
GitHub como texto plano.

## 7. Crear el backend en Render

1. En Render selecciona **New > Web Service**.
2. Conecta el repositorio `NexoTP`.
3. Selecciona la rama `main`.
4. Usa el plan gratuito.
5. Configura estos valores:

```text
Name: nexotp-api
Language: Python
Root Directory: dejar vacio
Build Command: pip install -r apps/backend/requirements.txt
Start Command: uvicorn apps.backend.app.main:app --host 0.0.0.0 --port $PORT --proxy-headers
Health Check Path: /api/health
```

En **Environment** agrega:

```text
APP_ENV=production
DATABASE_URL=postgresql+psycopg://...
SECRET_KEY=<clave generada>
ADMIN_PASSWORD_HASH=<hash generado>
ALLOWED_ORIGINS=https://URL-DEL-FRONTEND
```

Como todavia no conocemos la URL del frontend, puedes usar temporalmente:

```text
ALLOWED_ORIGINS=https://nexotp.onrender.com
```

Luego debes reemplazarla por la URL exacta que Render asigne al frontend.

No marques los secretos para mostrarlos en logs y no los copies a GitHub.

Pulsa **Create Web Service** y espera el despliegue.

Comprueba:

```text
https://nexotp-api.onrender.com/api/health
```

Debe responder aproximadamente:

```json
{"ok": true, "service": "NexoTP"}
```

La URL exacta puede ser diferente si el nombre ya estaba ocupado.

## 8. Conectar el frontend al backend

El frontend debe conocer la URL publica del backend mediante una variable de
compilacion:

```text
VITE_API_URL=https://nexotp-api.onrender.com
```

Antes de separar ambos servicios, el cliente debe usar esa variable para todas
las llamadas HTTP. No deben quedar URLs de desarrollo como:

```text
localhost:8000
127.0.0.1:8000
```

El codigo actual conserva una ruta de compatibilidad llamada
`/backend-page`. Antes del despliegue separado hay que completar este pequeño
ajuste en React para construir la direccion desde `VITE_API_URL`.

## 9. Crear el frontend en Render

Cuando el ajuste anterior este aplicado:

1. Selecciona **New > Static Site**.
2. Conecta el mismo repositorio.
3. Selecciona la rama `main`.
4. Configura:

```text
Name: nexotp
Root Directory: apps/frontend
Build Command: npm ci && npm run build
Publish Directory: dist
```

Agrega la variable:

```text
VITE_API_URL=https://nexotp-api.onrender.com
```

Configura una regla de reescritura para React Router:

```text
Source: /*
Destination: /index.html
Action: Rewrite
```

Publica el sitio y copia su URL definitiva.

## 10. Corregir CORS con la URL definitiva

Vuelve al servicio backend en Render y modifica:

```text
ALLOWED_ORIGINS=https://URL-REAL-DEL-FRONTEND
```

Ejemplo:

```text
ALLOWED_ORIGINS=https://nexotp.onrender.com
```

No uses `*` porque la aplicacion maneja sesiones y credenciales.

Render volvera a desplegar el backend después del cambio.

## 11. Probar el sitio publico

Abre una ventana privada del navegador y verifica:

1. Inicio publico.
2. Registro de egresado.
3. Inicio y cierre de sesion.
4. Edicion de perfil.
5. Feed y filtros.
6. Postulacion a una oferta.
7. Registro e ingreso de empresa.
8. Cambio de estado de postulacion.
9. Mensajeria.
10. Panel de institucion.
11. Administracion.
12. Descarga de PDF y CSV.
13. Vista en telefono.

Abre las herramientas del navegador y revisa las pestañas **Console** y
**Network**. No debe haber respuestas `500`, errores CORS ni llamadas a
`localhost`.

## 12. Comportamiento del plan gratuito

Render puede suspender el backend después de un periodo sin visitas. Al entrar
de nuevo:

- La primera solicitud puede tardar cerca de un minuto.
- Las siguientes solicitudes funcionan normalmente mientras siga activo.
- No se debe guardar información en el disco local de Render.
- Neon conserva la base PostgreSQL independientemente del reinicio del backend.

No uses servicios externos para golpear constantemente la aplicación e impedir
que duerma; puede incumplir las condiciones del proveedor.

## 13. Publicar cambios futuros

Cada vez que modifiques el proyecto:

```powershell
python -m pytest -q
Set-Location apps/frontend
npm run lint
npm run build
Set-Location ../..
git status
git add .
git commit -m "Describe el cambio"
git push
```

Render detectara el nuevo commit y volvera a desplegar los servicios.

## 14. Copias de seguridad

Aunque Neon tenga mecanismos de restauracion limitados, exporta periodicamente
una copia:

```powershell
pg_dump "TU_DATABASE_URL" --format=custom --file=nexotp-backup.dump
```

El archivo contiene datos sensibles:

- No lo subas a GitHub.
- Guardalo cifrado.
- Prueba que pueda restaurarse.
- Eliminalo de computadores compartidos.

## 15. Errores frecuentes

### El backend muestra un error de secretos

Comprueba que existan:

```text
APP_ENV=production
SECRET_KEY
ADMIN_PASSWORD_HASH
```

`SECRET_KEY` debe contener al menos 32 caracteres.

### Error de conexion PostgreSQL

Comprueba:

- Prefijo `postgresql+psycopg://`.
- `sslmode=require`.
- Contraseña completa.
- Que no se hayan perdido caracteres especiales al copiarla.

### Error CORS

`ALLOWED_ORIGINS` debe coincidir exactamente con el frontend, incluyendo
`https://` y sin una barra final.

### El despliegue no responde correctamente

Busca referencias a:

```text
localhost
127.0.0.1
sqlite
FLASK_DEBUG=1
```

### Error 404 al recargar una ruta React

Comprueba que exista la regla:

```text
/*  ->  /index.html  (Rewrite)
```

### La primera visita tarda mucho

Es el arranque en frio del servicio gratuito de Render. No necesariamente es
un error de NexoTP.

## 16. Mejoras posteriores

Cuando el sitio inicial esté estable:

1. Convertir completamente las vistas heredadas a una API JSON versionada.
2. Añadir Alembic para migraciones PostgreSQL.
3. Implementar CSRF para todas las operaciones autenticadas.
4. Añadir limitacion de intentos de inicio de sesion.
5. Separar almacenamiento de fotografías y archivos.
6. Automatizar pruebas y auditorias de dependencias en GitHub Actions.
7. Configurar un dominio propio cuando exista presupuesto.

## Referencias oficiales

- Render gratuito: <https://render.com/docs/free>
- Despliegue Python en Render: <https://render.com/docs/deploy-flask>
- Neon: <https://neon.com/docs/introduction>
- Neon Free: <https://neon.com/pricing>
- Cloudflare Pages como alternativa futura: <https://developers.cloudflare.com/pages/>
