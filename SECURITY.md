# Seguridad

No publiques secretos, bases de datos ni archivos `.env`. Los incidentes o
vulnerabilidades deben comunicarse de forma privada al responsable del proyecto.

En produccion son obligatorias `SECRET_KEY`, `ADMIN_PASSWORD_HASH`, `DATABASE_URL` y
`ALLOWED_ORIGINS`. La aplicacion rechaza el arranque si los secretos principales
no estan presentes o la clave de sesion es demasiado corta.

## Lista previa a publicar

- HTTPS activo en el proxy o proveedor.
- PostgreSQL con respaldos y usuario de privilegios minimos.
- Variables configuradas en el administrador de secretos del proveedor.
- CORS limitado al dominio publico.
- `APP_ENV=production` y depuracion desactivada.
- Dependencias auditadas y pruebas ejecutadas.
- Restauracion de una copia de seguridad verificada.
