# Deploy en Render (Flask + DB en la nube)

## 1) Preparar GitHub
En tu proyecto local:
```bash
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

## 2) Crear servicio web en Render
1. Dashboard Render > New > Web Service.
2. Conectar repo GitHub.
3. Runtime: Python.
4. Build Command:
```bash
pip install -r requirements.txt
```
5. Start Command:
```bash
gunicorn app:app
```

## 3) Variables de entorno
Configura en Render:
- `SECRET_KEY`
- `ADMIN_PASSWORD`
- `DATABASE_URL` (si usas Postgres)

## 4) Base de datos recomendada
Usar PostgreSQL administrado (Render Postgres o Neon/Supabase).

## 5) Ajuste de app.py (sugerido)
Usar `DATABASE_URL` en nube y SQLite solo en local.

Patron recomendado:
```python
db_url = os.environ.get("DATABASE_URL", "sqlite:///nexotp.db")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
```

## 6) Deploy continuo
Cada `git push` a `main` gatilla redeploy automatico.

## 7) Validacion post deploy
- Abrir URL publica de Render.
- Probar login usuario/empresa.
- Publicar oferta y postular.
- Verificar filtros del panel empresa.

## 8) Notas
- SQLite no es ideal para produccion multiusuario.
- Para produccion usar Postgres + backups.
