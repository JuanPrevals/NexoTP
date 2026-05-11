# 🚀 10 Funcionalidades para agregar a NexoTP

Basado en el análisis de la **Propuesta.docx** (Design Thinking del Liceo Vate Vicente Huidobro) y el estado actual del proyecto.

---

## 1. 💬 Sistema de Mensajería entre Usuario y Empresa

> **Problema de la propuesta:** Los egresados no saben cómo presentar formalmente sus competencias ante empleadores.

Agregar un chat interno que permita a las empresas comunicarse directamente con los postulantes. Actualmente, cuando una empresa acepta/rechaza, solo deja un motivo estático. Un sistema de mensajes permitiría:
- Coordinar entrevistas
- Pedir documentos adicionales
- Dar feedback directo al egresado

**Modelo sugerido:** `Mensaje(id, remitente_tipo, remitente_id, destinatario_tipo, destinatario_id, postulacion_id, contenido, leido, fecha)`

---

## 2. 📊 Dashboard de Estadísticas para el Egresado

> **Problema de la propuesta:** Los egresados se frustran y pierden motivación al no ver resultados.

Crear un panel personal que muestre:
- Total de postulaciones enviadas vs. respuestas recibidas
- Tasa de aceptación
- Ofertas recomendadas según su especialidad
- Gráfico de actividad (postulaciones por semana)
- Comparación anónima con otros egresados de su misma especialidad

Esto combate directamente la **Consecuencia 2** del documento: desmotivación y pérdida de autoestima.

---

## 3. 🎓 Sistema de Mentoría Integrado

> **Problema de la propuesta:** 3 de 5 entrevistados aceptarían prácticas no remuneradas si incluyen mentoría.

El campo `incluye_mentoria` ya existe en las ofertas pero no tiene funcionalidad real. Agregar:
- Perfil de mentor (profesional asignado por la empresa)
- Calendario de sesiones de mentoría
- Registro de objetivos y avances del egresado
- Evaluación del mentor al finalizar la práctica

---

## 4. 📄 Generador Automático de CV/Portafolio

> **Problema de la propuesta:** Los egresados de Programación no saben construir un portafolio visible para empleadores. Los de Contabilidad/RRHH no tienen documentación formal.

Agregar un botón "Generar CV" que tome los datos del perfil del usuario y los exporte como PDF profesional. Incluir:
- Plantillas diferenciadas por especialidad (Contabilidad, RRHH, Logística, Programación)
- Sección de proyectos escolares con enlaces
- QR code con enlace al perfil público de NexoTP
- Exportación en PDF

**Librería sugerida:** `weasyprint` o `reportlab` para generar PDFs desde Flask.

---

## 5. 🔔 Sistema de Notificaciones en Tiempo Real

> **Problema de la propuesta:** Ningún entrevistado conocía plataformas específicas de inserción laboral TP.

Actualmente el feed de novedades existe pero es pasivo. Agregar:
- Notificaciones push/email cuando una empresa responde a una postulación
- Alerta cuando se publica una oferta que matchea la especialidad del usuario
- Badge de notificaciones no leídas en la navbar
- Notificación por email (usando Flask-Mail) para eventos críticos

**Modelo sugerido:** `Notificacion(id, usuario_id, tipo, titulo, contenido, leida, fecha)`

---

## 6. 🤝 Matching Inteligente Egresado-Oferta

> **Problema de la propuesta:** Desconexión entre el currículo escolar y las necesidades del mercado laboral.

Implementar un algoritmo de compatibilidad que:
- Compare las habilidades del usuario con los requisitos de la oferta
- Muestre un porcentaje de match (ej: "85% compatible")
- Priorice ofertas por compatibilidad en el feed
- Sugiera al usuario qué habilidades le faltan para calificar

```python
def calcular_match(usuario, oferta):
    habilidades_usuario = set(usuario.habilidades_lista)
    requisitos_oferta = set(oferta.requisitos_lista)
    if not requisitos_oferta:
        return 100
    coincidencias = habilidades_usuario & requisitos_oferta
    return int(len(coincidencias) / len(requisitos_oferta) * 100)
```

---

## 7. 🏢 Perfiles Públicos de Empresa con Reseñas

> **Problema de la propuesta:** Las PYMEs carecen de mecanismos para contratar jóvenes sin experiencia.

Agregar páginas públicas de cada empresa con:
- Descripción completa y fotos
- Ofertas activas e históricas
- Reseñas de egresados que ya trabajaron ahí
- Indicador "Amigable con egresados TP" (badge verificado)
- Estadísticas: cantidad de egresados contratados, tasa de aceptación

Esto genera confianza mutua, respondiendo a la pregunta de las entrevistas: *"¿Qué debería tener para que confiaras en él?"*

---

## 8. 📅 Módulo de Prácticas Profesionales y Seguimiento

> **Problema de la propuesta:** La situación se agudiza a partir de noviembre, cuando los egresados buscan su primera inserción laboral.

Crear un flujo específico para prácticas profesionales:
- Las empresas pueden publicar ofertas de tipo "Práctica" con fecha de inicio/fin
- El liceo puede aprobar/supervisar la práctica desde un panel especial
- Registro de horas y evaluaciones periódicas
- Certificado digital al completar la práctica
- Convenio digital empresa-liceo

---

## 9. 📈 Panel de Impacto para el Liceo (Rol Institucional)

> **Problema de la propuesta:** El liceo necesita demostrar el impacto real del convenio PTECH-IBM.

Agregar un rol "Liceo/Institución" con dashboard que muestre:
- Cantidad de egresados registrados por generación
- Tasa de inserción laboral por especialidad
- Empresas aliadas activas
- Tiempo promedio entre egreso y primer empleo
- Reportes exportables para MINEDUC y sostenedores
- Métricas del programa PTECH-IBM

**Modelo sugerido:** `Institucion(id, nombre, rut, tipo, admin_email, password_hash)`

---

## 10. 🌐 Mapa Interactivo de Oportunidades por Comuna

> **Problema de la propuesta:** El problema afecta a comunas del sector sur: San Ramón, La Pintana, El Bosque, La Granja, Pedro Aguirre Cerda.

Integrar un mapa usando Leaflet.js que muestre:
- Ubicación de empresas con ofertas activas
- Filtro por comuna y especialidad
- Radio de búsqueda desde la ubicación del egresado
- Densidad de oportunidades por zona
- Rutas de transporte público cercanas (integración con datos abiertos de Santiago)

Esto es especialmente relevante porque los usuarios prefieren ofertas cercanas a su comuna y el transporte es un factor real para jóvenes de quintiles 1-2.

---

## Resumen de Prioridad

| # | Funcionalidad | Impacto | Dificultad | Prioridad |
|---|---|---|---|---|
| 1 | Mensajería Usuario-Empresa | 🔴 Alto | 🟡 Media | ⭐⭐⭐⭐⭐ |
| 2 | Dashboard Estadísticas | 🟡 Medio | 🟢 Baja | ⭐⭐⭐⭐ |
| 3 | Sistema de Mentoría | 🔴 Alto | 🔴 Alta | ⭐⭐⭐⭐ |
| 4 | Generador de CV/PDF | 🔴 Alto | 🟡 Media | ⭐⭐⭐⭐⭐ |
| 5 | Notificaciones | 🟡 Medio | 🟡 Media | ⭐⭐⭐⭐ |
| 6 | Matching Inteligente | 🔴 Alto | 🟢 Baja | ⭐⭐⭐⭐⭐ |
| 7 | Perfiles Públicos Empresa | 🟡 Medio | 🟢 Baja | ⭐⭐⭐ |
| 8 | Módulo de Prácticas | 🔴 Alto | 🔴 Alta | ⭐⭐⭐⭐ |
| 9 | Panel Liceo/Institución | 🟡 Medio | 🟡 Media | ⭐⭐⭐ |
| 10 | Mapa Interactivo | 🟡 Medio | 🟡 Media | ⭐⭐⭐ |

> [!TIP]
> Las funcionalidades **1, 4 y 6** son las más rápidas de implementar con mayor impacto directo según los datos de las entrevistas de la propuesta.
