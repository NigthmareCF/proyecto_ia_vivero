# SAGA FLOW - modulo reports

## Objetivo

Centralizar la generacion de reportes PDF y la configuracion/envio de notificaciones a partir de resultados de patrullaje.

## Flujo principal

1. usuario autenticado solicita generar reporte
2. backend valida consistencia de conteos y usuario generador
3. se persiste el `Report`
4. se genera el PDF localmente en `/app/images/reports`
5. se actualiza la ruta `pdfPath`
6. el usuario puede descargar el PDF o notificarlo por canales activos

## Flujo de notificaciones

1. usuario define sus canales activos en `notification_config`
2. solicita `POST /api/reports/notify`
3. el backend filtra configuraciones activas del usuario
4. cada proveedor envia un mensaje con referencia al reporte
5. email adjunta el PDF; SMS, WhatsApp y Telegram envian resumen y ruta

## Nota de integracion futura

En esta rama el modulo `reports` referencia `patrolId` como campo escalar.
Cuando se integre con `patrols`, el servicio podra enriquecerse con entidades reales sin reestructurar el contrato principal del modulo.
