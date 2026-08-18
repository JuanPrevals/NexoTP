import type { CapacitorConfig } from '@capacitor/cli'

const productionUrl = (process.env.NEXOTP_APP_URL || 'https://p01--nexotp-api--jwyjydpmw5fj.code.run').replace(/\/$/, '')

const config: CapacitorConfig = {
  appId: 'cl.nexotp.app',
  appName: 'NexoTP',
  webDir: 'dist',
  server: {
    url: productionUrl,
    cleartext: false,
    androidScheme: 'https',
  },
  android: {
    allowMixedContent: false,
    backgroundColor: '#f7f8f6',
  },
}

export default config
