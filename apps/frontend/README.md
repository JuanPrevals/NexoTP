# Frontend React de NexoTP

Cliente React 19 creado con Vite. Consume el gateway FastAPI en el puerto 8000
y conserva las rutas, formularios, sesiones y estilos del sistema NexoTP.

```bash
npm install
npm run dev
```
# Android

La app Android usa Capacitor y carga el despliegue web completo para conservar
sesiones, formularios, mapas, mensajeria y eventos en tiempo real en el mismo
origen. La URL predeterminada es el despliegue de produccion documentado.

Para usar otro dominio y generar un APK instalable en Windows:

```powershell
$env:NEXOTP_APP_URL = "https://tu-dominio-nexotp.cl"
npm run android:apk
```

Se requiere Android Studio o el Android SDK configurado en `ANDROID_HOME`. El
APK se crea en `android/app/build/outputs/apk/debug/app-debug.apk`.
