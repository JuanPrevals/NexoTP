# Avisos de terceros

La integracion empresarial con el SII sigue el flujo tecnico documentado por
[`sagmor/sii_chile`](https://github.com/sagmor/sii_chile), distribuido bajo
licencia MIT. NexoTP contiene una implementacion propia en Python, limitada a
RUT de personas juridicas y con controles adicionales de privacidad, tiempo
maximo, cache y frecuencia de consulta.

Ni ese proyecto ni NexoTP estan afiliados o respaldados por el Servicio de
Impuestos Internos. La respuesta es informativa y no certifica el
comportamiento tributario de una empresa.

No se integro `mavilchesb/Buscar-por-RUT` porque su codigo cliente depende del
antiguo despliegue publico de `sii_chile` y permitiria consultas arbitrarias
desde el navegador. La consulta de NexoTP se ejecuta exclusivamente en el
backend.
