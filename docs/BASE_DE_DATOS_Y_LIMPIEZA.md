# Ver y limpiar la base de datos de NexoTP

## Ver los datos desde Neon

1. Entra en [Neon Console](https://console.neon.tech/).
2. Abre el proyecto y la rama que usa `DATABASE_URL` en Northflank.
3. En **Tables** puedes navegar por las tablas y sus filas.
4. En **SQL Editor** puedes ejecutar consultas sin instalar programas.

Consultas de solo lectura utiles:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

SELECT COUNT(*) AS usuarios FROM usuario;
SELECT COUNT(*) AS empresas FROM empresa;
SELECT COUNT(*) AS ofertas FROM oferta;
SELECT COUNT(*) AS postulaciones FROM postulacion;

SELECT id, nombre, apellido, email, fecha_registro
FROM usuario
ORDER BY fecha_registro DESC;

SELECT id, nombre, email, fecha_registro
FROM empresa
ORDER BY fecha_registro DESC;
```

No pegues `DATABASE_URL`, contrasenas ni hashes en capturas o chats. Si una cadena se hace publica, rota la contrasena en Neon y actualiza `DATABASE_URL` en Northflank.

## Eliminar los datos demo existentes

El despliegue nuevo ya no crea datos ficticios: `SEED_DEMO_DATA` esta desactivado por defecto. Para limpiar los registros que ya existen, primero despliega esta version y abre **Northflank > nexotp-api > Observe > Shell**.

Ejecuta primero la vista previa:

```bash
python -m apps.backend.scripts.cleanup_demo_data
```

Comprueba que solo enumera las tres cuentas de egresado, tres empresas y una institucion demo. Luego confirma:

```bash
python -m apps.backend.scripts.cleanup_demo_data --confirm DELETE_DEMO_DATA
```

La herramienta elimina solo las identidades demo conocidas y sus registros relacionados. No usa nombres genericos ni elimina tablas completas.

## Usar datos demo solo en desarrollo

Si alguna vez necesitas volver a cargar ejemplos en un entorno desechable, define:

```env
SEED_DEMO_DATA=1
```

No configures esa variable en Northflank.
