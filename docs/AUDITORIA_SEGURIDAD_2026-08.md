# Auditoria defensiva de seguridad

Revision realizada con la metodologia y herramientas defensivas de `Masriyan/Claude-Code-CyberSecurity-Skill`.

## Corregido

- Proteccion CSRF para todas las solicitudes que modifican estado.
- Eliminado el `drop_all()` automatico ante errores de base de datos.
- Sembrado demo desactivado por defecto.
- Estadisticas internas limitadas al administrador.
- Contrasenas nuevas con minimo de 10 caracteres.
- CSP y HSTS agregados a Nginx.
- Contexto Docker reducido con `.dockerignore` para no enviar secretos ni archivos locales al build.
- Credenciales demo retiradas de las pantallas de acceso.

## Resultados

- Auditor de dependencias Python/OSV: 0 vulnerabilidades conocidas en 11 dependencias declaradas.
- `npm audit --omit=dev`: 0 vulnerabilidades.
- Auditor de configuracion Nginx: 7 de 7 controles aprobados (100%).
- Pruebas automatizadas: 6 aprobadas.

## Trabajo recomendado antes de manejar datos sensibles

- Agregar limitacion de intentos de inicio de sesion mediante un almacen compartido.
- Cambiar el cierre de sesion de GET a POST protegido por CSRF.
- Sustituir la creacion implicita de tablas por migraciones versionadas (Alembic).
- Fijar versiones y hashes de dependencias Python e imagenes Docker.
- Configurar copias de seguridad y recuperacion en Neon.
- Añadir monitoreo de errores y alertas sin registrar secretos ni datos personales.

Esta revision reduce riesgos comunes, pero no constituye una certificacion ni garantiza ausencia total de vulnerabilidades.
