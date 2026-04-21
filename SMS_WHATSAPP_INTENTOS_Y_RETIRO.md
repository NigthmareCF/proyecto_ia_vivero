# Registro de Intentos: SMS y WhatsApp para Reportes

Fecha de cierre: 2026-04-20

## Objetivo

Se intentó habilitar el envio de reportes por `SMS` y `WhatsApp` desde el modulo `reports`, manteniendo `EMAIL` como canal principal con PDF adjunto y agregando para mensajeria un resumen textual mas un enlace descargable al PDF.

## Lo que se implementó

- Soporte de canales `EMAIL`, `SMS` y `WHATSAPP` en `NotificationChannel`.
- Lectura del `phoneNumber` desde el perfil de usuario para `SMS` y `WHATSAPP`.
- Resumen textual del reporte para mensajeria:
  - `Reporte No.x`
  - `Detalles`
  - `Patrullaje No.x`
  - conteos `Sano / Atencion / Peligro / Observaciones`
  - fecha de emision
  - enlace `Consulta de reporte documentada y detallada`
- Endpoint publico para descarga del PDF del reporte por token.

## Intentos realizados

### 1. Twilio SMS

Se integró Twilio para envio de `SMS`.

Resultado:
- Hubo envios aceptados por SDK/API.
- Luego aparecio el limite diario de la cuenta:
  - `exceeded the 5 daily messages limit`

Problemas:
- Limite de cuenta.
- Entrega inconsistente para pruebas repetidas.
- Dependencia operativa de credenciales y cuotas.

### 2. Twilio WhatsApp

Se integró Twilio para `WhatsApp`, usando el sandbox y remitente `whatsapp:+14155238886`.

Resultado:
- Hubo solicitudes aceptadas por la API.
- Se recibieron pruebas en algunos casos.

Problemas:
- Dependencia del sandbox y politicas de Twilio/WhatsApp.
- Mayor complejidad operativa para algo que no era core del MVP.

### 3. Vonage SMS

Se integró Vonage como alternativa de `SMS`.

Resultado:
- Se implementó el cliente y el backend quedó preparado.
- Las credenciales recibidas fueron inconsistentes en distintas pruebas.
- Hubo respuestas tipo `401 Unauthorised: Invalid Token`.
- En pruebas donde la API no lanzó excepcion, no se confirmó entrega final en los numeros destino.

Problemas:
- Credenciales ambiguas.
- Falta de confirmacion de entrega real.
- Mas tiempo invertido en soporte que en valor de producto.

### 4. AWS SNS SMS

Se integró AWS SNS como otra alternativa de `SMS`, usando `SNS` con credenciales cargadas desde archivo y/o entorno.

Resultado:
- El backend compiló y ejecutó pruebas manuales sin excepción.
- La API aceptó solicitudes de prueba.

Problemas:
- La aceptacion del request no garantizó visibilidad clara de entrega final en el flujo de producto.
- Ya se había invertido demasiado tiempo en varios proveedores.

## Decisión tomada

Se retira el soporte de `SMS` y `WHATSAPP` del modulo `reports`.

Motivos:
- No eran críticos para cerrar el proyecto.
- `EMAIL` ya funciona con PDF real adjunto.
- Los intentos con varios proveedores consumieron demasiado tiempo de integración y validación.
- La solución más estable y suficiente para esta fase es correo electrónico.

## Estado final decidido

- `EMAIL` se conserva como único canal de envio de reportes.
- `SMS` y `WHATSAPP` se eliminan del código del modulo `reports`.
- Se conserva este documento como registro técnico de lo intentado y por qué se descartó.
