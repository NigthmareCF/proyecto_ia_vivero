# Proyecto Completo: Levantamiento con Docker

Esta rama contiene el stack completo para levantar el sistema principal desde CLI.

## 1. Preparar variables

```bash
cp .env.example .env
```

Ajusta como mínimo:

- `JWT_SECRET`
- `MAIL_HOST`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM`
- `MAIL_SMTP_AUTH`, `MAIL_SMTP_STARTTLS_ENABLE`, `MAIL_SMTP_STARTTLS_REQUIRED`
- `CORS_ALLOWED_ORIGINS`
- `VITE_API_URL`
- `VITE_WS_URL`

## 2. Construir y levantar local con Nginx

```bash
docker compose up --build -d
```

El frontend se compila y se sirve desde Nginx. La entrada local queda en `http://localhost:3000`; Nginx proxyea `/api` y `/api/ws` al backend interno. En despliegues con dominio, el mismo Nginx puede atender `agrotechnologyrobotics.com` y `www.agrotechnologyrobotics.com` como front door unico.

## 3. Revisar estado

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
```

## 4. URLs esperadas

- Frontend: `http://localhost:3000`
- API por Nginx: `http://localhost:3000/api`
- Backend directo para depuracion: `http://localhost:8080/api`
- Healthcheck por Nginx: `http://localhost:3000/health`
- Healthcheck backend: `http://localhost:8080/api/actuator/health`

Para dominio publico:

- Frontend: `https://agrotechnologyrobotics.com`
- API por Nginx: `https://agrotechnologyrobotics.com/api`
- WebSocket por Nginx: `wss://agrotechnologyrobotics.com/api/ws`

## 5. Reconstruir si cambian dependencias o Dockerfiles

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

## 6. Observacion

El runtime de la Raspberry Pi se levanta aparte desde la rama `robot-pi`, con su propio `docker-compose.yml`.

## 7. Despliegue tipo VM con Nginx

Para una VM GCP o una instancia pública, usa `docker-compose.vm.yml`:

```bash
cp .env.vm.example .env.vm
docker compose --env-file .env.vm -f docker-compose.vm.yml up --build -d
```

Ese stack:

- sirve el frontend compilado desde Nginx en `80`
- proxyea `/api` y `/api/ws` al backend interno
- deja al backend sin exposición pública directa
- usa la misma configuracion Nginx validada localmente

## 8. VLM local en VM GPU

El compose de VM incluye `vlm-qwen` como servicio interno. No se descarga nada en la laptop al editar el proyecto; la imagen `vllm/vllm-openai` y el modelo Qwen se descargan cuando se levanta el stack en la VM:

```bash
docker compose --env-file .env.vm -f docker-compose.vm.yml up --build -d
```

Valores por defecto en `.env.vm.example`:

- `VLM_QWEN_MODEL=Qwen/Qwen2.5-VL-7B-Instruct-AWQ`
- `VLM_SERVED_MODEL_NAME=qwen-vl-local`
- `VISION_LOCAL_VLM_URL=http://vlm-qwen:8000/v1`
- `VISION_API_MODEL=gemini-2.5-flash`
- `VISION_PATROL_CLASSIFIER_ENABLED=true`
- `VISION_PATROL_GEMINI_REPORT_ENABLED=true`

Requisitos de la VM:

- GPU NVIDIA disponible para Docker
- driver NVIDIA operativo (`nvidia-smi`)
- NVIDIA Container Toolkit instalado
- no exponer el puerto `8000` a internet; solo lo usa el backend dentro de la red Docker

## 8.1 Gemini en laboratorio

Para que el backend use Gemini en este equipo, levanta `release` con un `.env` local que tenga:

```bash
VISION_API_ENABLED=true
VISION_API_PROVIDER=gemini
GEMINI_API_KEY=tu_clave_local
```

El secreto no debe subirse al repositorio. El compose de `release` ya expone estas variables al backend.

## 9. SMTP Relay por IP

Para Google Workspace SMTP Relay por IP, el backend debe levantarse con:

```bash
MAIL_HOST=smtp-relay.gmail.com
MAIL_PORT=587
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=reportes@tu-dominio-workspace.com
MAIL_SMTP_AUTH=false
MAIL_SMTP_STARTTLS_ENABLE=true
MAIL_SMTP_STARTTLS_REQUIRED=true
MAIL_SMTP_ENVELOPE_FROM=reportes@tu-dominio-workspace.com
MAIL_SMTP_LOCALHOST=tu-dominio-workspace.com
```

Si Google devuelve `550-5.7.1 Invalid credentials for relay`, el backend ya llego al relay, pero la IP publica, el dominio del remitente o el EHLO/envelope-from no coincide con lo autorizado en Google Workspace.
