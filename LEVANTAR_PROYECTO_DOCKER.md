# Proyecto Completo: Levantamiento con Docker

Esta rama contiene el stack completo para levantar el sistema principal desde CLI.

## 1. Preparar variables

```bash
cp .env.example .env
```

Ajusta como mínimo:

- `JWT_SECRET`
- `MAIL_HOST`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM`
- `CORS_ALLOWED_ORIGINS`
- `VITE_API_URL`
- `VITE_WS_URL`

## 2. Construir y levantar

```bash
docker compose up --build -d
```

## 3. Revisar estado

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
```

## 4. URLs esperadas

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8080/api`
- Healthcheck: `http://localhost:8080/api/actuator/health`

## 5. Reconstruir si cambian dependencias o Dockerfiles

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

## 6. Observacion

El runtime de la Raspberry Pi se levanta aparte desde la rama `robot-pi`, con su propio `docker-compose.yml`.
