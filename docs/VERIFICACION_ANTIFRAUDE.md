# Verificacion antifraude de NexoTP

## Variables necesarias en Northflank

La verificacion por correo requiere estas variables de runtime en `nexotp-api`:

```env
SMTP_HOST=smtp.tu-proveedor.com
SMTP_PORT=587
SMTP_USER=usuario-smtp
SMTP_PASSWORD=contrasena-smtp
MAIL_FROM=verificacion@tu-dominio.cl
PUBLIC_ORIGIN=https://p01--nexotp-api--jwyjydpmw5fj.code.run
```

Guarda `SMTP_PASSWORD` como secreto. Despues usa **Update & restart**. NexoTP no registra tokens ni direcciones de verificacion en los logs.

## Flujo de usuarios

1. El usuario crea su cuenta.
2. Recibe un enlace de un solo uso, valido durante 24 horas.
3. Mientras el correo este pendiente puede navegar, pero no postular ni enviar mensajes.
4. El administrador puede otorgar el sello de identidad verificada tras comprobarla por un canal institucional.
5. Una cuenta suspendida pierde su sesion y deja de tener perfil publico.

## Flujo de empresas

1. La empresa ingresa un RUT de persona juridica y NexoTP consulta su existencia en el servicio publico del SII.
2. Si existe, se completan razon social, actividad economica e inicio de actividades. Esos datos, junto con el responsable, no son publicos.
3. Verifica su correo mediante un enlace de un solo uso.
4. El administrador revisa los antecedentes y aprueba o rechaza la cuenta.
5. Solo una empresa aprobada puede aparecer en el directorio, publicar ofertas y enviar mensajes.
6. Cambiar los datos de verificacion devuelve la cuenta al estado `Pendiente`.

Las consultas se hacen desde el backend, admiten solo RUT de personas juridicas, tienen un limite de cinco intentos cada diez minutos y no permiten buscar nombres de personas. El SII es un servicio externo: una interrupcion temporal impide completar una nueva verificacion, pero no afecta las cuentas ya verificadas.

## Operacion administrativa

En `/admin-nexotp/panel` se puede:

- verificar o retirar el sello de identidad de un usuario;
- aprobar, rechazar, suspender o reactivar empresas;
- suspender o reactivar usuarios;
- revisar y resolver reportes;
- consultar el historial de acciones antifraude.

Antes de aprobar una empresa, contrasta el RUT y razon social con una fuente oficial y confirma que el responsable controla el correo o dominio informado. El sello significa que NexoTP realizo esa revision; no debe concederse automaticamente.

## Reportes

Usuarios y empresas autenticados pueden reportar perfiles, empresas, ofertas y mensajes. Los mensajes solo pueden reportarlos participantes de la conversacion. Un reporte no suspende automaticamente una cuenta: queda pendiente para evitar abuso del sistema de denuncias.

## Despliegue sobre una base existente

Al iniciar la nueva version se agregan las columnas y tablas necesarias sin borrar datos. Las empresas existentes quedan pendientes y sus ofertas dejan de ser publicas hasta que:

1. completen los datos desde su panel;
2. verifiquen el correo;
3. sean aprobadas por administración.

Esto es intencional para evitar que cuentas antiguas omitan el nuevo control.
