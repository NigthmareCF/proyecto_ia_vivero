# Pruebas Manuales Reports con Email Real

Fecha: 2026-04-04
Usuario SMTP temporal: `ferchocastfun15@gmail.com`
Nombre visible del correo: `Fernando CastFun`
Destino temporal de prueba: `ferchocastfun15@gmail.com`

## Objetivo

Validar de nuevo el modulo `reports` con datos temporales y confirmar personalmente la recepcion de un correo real con el PDF adjunto.

## Requisitos previos

1. base de datos disponible
2. usuario seed funcional:
   - email: `admin@vivero.com`
   - password: `Admin2026!`
3. levantar el backend con variables temporales en PowerShell

## Arranque local correcto del backend

Para esta validacion, se trabajara con variables temporales en PowerShell, incluyendo SMTP real y PostgreSQL local.

Bloque unico completo:

```powershell
$env:SPRING_PROFILES_ACTIVE="dev"
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
$env:DB_NAME="vivero_db"
$env:DB_USERNAME="vivero_user"
$env:DB_PASSWORD="vivero_pass"
$env:MAIL_HOST="smtp.gmail.com"
$env:MAIL_PORT="587"
$env:MAIL_USERNAME="ferchocastfun15@gmail.com"
$env:MAIL_PASSWORD="WhiteFang1907"
$env:MAIL_FROM="ferchocastfun15@gmail.com"
$env:SERVER_PORT="8080"
mvn --% spring-boot:run -Dspring-boot.run.jvmArguments=-Dspring.devtools.restart.enabled=false
```

Si el puerto `8080` ya esta ocupado, usar:

```powershell
$env:SERVER_PORT="8081"
mvn --% spring-boot:run -Dspring-boot.run.jvmArguments=-Dspring.devtools.restart.enabled=false
```

En ese caso, todas las pruebas de Postman deben apuntar a:

```text
http://localhost:8081/api
```

## Configuracion SMTP acordada para esta prueba

Si se quiere dejar tambien en `.env`, los valores temporales acordados son:

```env
MAIL_HOST=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=ferchocastfun15@gmail.com
MAIL_PASSWORD=WhiteFang1907
MAIL_FROM=ferchocastfun15@gmail.com
```

Notas:

- `MAIL_FROM` conviene que sea igual a `MAIL_USERNAME`.
- si esto no esta bien, `POST /reports/notify` puede terminar en `500 INTERNAL_ERROR`
- para una prueba real estable, usar el correo completo autentico tanto en `MAIL_USERNAME` como en `MAIL_FROM`
- el nombre visible `Fernando CastFun` no se configura en `MAIL_USERNAME`; ahi siempre va el correo real completo
- si Gmail rechaza autenticacion SMTP, la causa probable no sera Postman sino la credencial usada para SMTP

## Orden correcto de pruebas

### 1. Login

Que hace:

- autentica al usuario admin y devuelve JWT

Request:

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "admin@vivero.com",
  "password": "Admin2026!"
}
```

Que debe devolver en Postman:

- status `200 OK`
- `success: true`
- `message: Login successful`
- `data.accessToken`
- `data.refreshToken`
- `data.tokenType = Bearer`
- `data.email = admin@vivero.com`
- `data.role = ADMIN`

Dato a buscar y guardar:

- copiar `data.accessToken`

### 2. Consultar canales soportados

Que hace:

- confirma que el backend expone los canales del enum de notificacion

Request:

```http
GET /api/reports/notifications/channels
Authorization: Bearer TU_TOKEN
```

Que debe devolver en Postman:

- status `200 OK`
- `message: Supported notification channels retrieved`
- `data` con:
  - `EMAIL`
  - `SMS`
  - `WHATSAPP`
  - `TELEGRAM`

### 3. Revisar configuracion actual

Que hace:

- muestra las configuraciones de notificacion asociadas al usuario autenticado

Request:

```http
GET /api/reports/notifications/config
Authorization: Bearer TU_TOKEN
```

Que debe devolver en Postman:

- status `200 OK`
- `message: Notification configs retrieved`
- una lista de configuraciones

Dato a buscar:

- confirmar si existe `EMAIL`
- confirmar si `active` esta en `true`

### 4. Guardar EMAIL real temporal

Que hace:

- deja el canal `EMAIL` apuntando a `ferchocastfun15@gmail.com`

Request:

```http
PUT /api/reports/notifications/config/EMAIL
Authorization: Bearer TU_TOKEN
Content-Type: application/json

{
  "contactValue": "ferchocastfun15@gmail.com",
  "active": true
}
```

Que debe devolver en Postman:

- status `200 OK`
- `message: Notification channel config saved`
- `data.channel = EMAIL`
- `data.contactValue = ferchocastfun15@gmail.com`
- `data.active = true`

### 5. Crear reporte temporal nuevo

Que hace:

- crea un reporte nuevo
- genera PDF
- devuelve el `id` real que debes usar en las siguientes pruebas

Request:

```http
POST /api/reports
Authorization: Bearer TU_TOKEN
Content-Type: application/json

{
  "patrolId": 3001,
  "title": "Real email delivery validation",
  "summary": "Temporary report created to validate real email delivery.",
  "observationsCount": 4,
  "healthyCount": 1,
  "attentionCount": 2,
  "dangerCount": 1
}
```

Que debe devolver en Postman:

- status `201 Created`
- `message: Report generated successfully`
- `data.id` con el id real del reporte
- `data.pdfPath` no vacio
- `data.generatedByEmail = admin@vivero.com`

Dato a buscar y guardar:

- copiar `data.id`

### 6. Consultar el reporte creado

Que hace:

- verifica que el reporte realmente existe y confirma sus datos finales

Request:

```http
GET /api/reports/{REPORT_ID}
Authorization: Bearer TU_TOKEN
```

Que debe devolver en Postman:

- status `200 OK`
- `message: Report retrieved`
- `data.id = REPORT_ID`
- `data.title = Real email delivery validation`

### 7. Descargar PDF del reporte creado

Que hace:

- valida que el PDF generado se puede abrir desde el endpoint

Request:

```http
GET /api/reports/{REPORT_ID}/pdf
Authorization: Bearer TU_TOKEN
```

Que debe devolver en Postman:

- status `200 OK`
- `Content-Type: application/pdf`
- visualizacion o descarga del archivo PDF

### 8. Enviar notificacion real por email

Que hace:

- toma el reporte creado
- busca la configuracion activa `EMAIL`
- genera el PDF en memoria
- intenta enviarlo al correo configurado

Request:

```http
POST /api/reports/notify
Authorization: Bearer TU_TOKEN
Content-Type: application/json

{
  "reportId": REPORT_ID,
  "channels": ["EMAIL"]
}
```

Que debe devolver en Postman si SMTP esta bien:

- status `200 OK`
- `success: true`
- `message: Report notified successfully`
- `data: Sent channels: 1`

Verificacion manual adicional:

- revisar bandeja de entrada de `ferchocastfun15@gmail.com`
- revisar spam/promociones si no aparece en inbox
- confirmar que el correo trae adjunto `report-{REPORT_ID}.pdf`

Que puede devolver si SMTP esta mal:

- status `500 Internal Server Error`
- `message: Error interno del servidor`
- `error: INTERNAL_ERROR`

Interpretacion:

- en ese caso el endpoint llego hasta el proveedor de correo, pero fallo el envio real o su manejo de excepcion

## Pruebas negativas que siguen siendo correctas

### A. Email invalido

Request:

```http
PUT /api/reports/notifications/config/EMAIL
Authorization: Bearer TU_TOKEN
Content-Type: application/json

{
  "contactValue": "correo-invalido",
  "active": true
}
```

Resultado esperado:

- status `400 Bad Request`
- `message: Invalid email format`
- `error: INVALID_EMAIL_CONTACT`

### B. Conteos inconsistentes

Request:

```http
POST /api/reports
Authorization: Bearer TU_TOKEN
Content-Type: application/json

{
  "patrolId": 3002,
  "title": "Broken report",
  "summary": "Should fail.",
  "observationsCount": 4,
  "healthyCount": 1,
  "attentionCount": 1,
  "dangerCount": 1
}
```

Resultado esperado:

- status `400 Bad Request`
- `message: State counts must match total observations`
- `error: INVALID_REPORT_COUNTS`

## Criterio de cierre

La validacion principal queda correcta si pasan estos puntos:

1. se guarda `EMAIL` con `ferchocastfun15@gmail.com`
2. se crea un reporte nuevo con `201`
3. el PDF del reporte nuevo descarga bien
4. `POST /reports/notify` devuelve `200`
5. el correo llega realmente con el PDF adjunto
