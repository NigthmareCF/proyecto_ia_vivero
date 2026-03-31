# Proyecto IA Vivero

Base tecnica del repositorio para el sistema de monitoreo autonomo de viveros.

## Alcance de esta rama

La rama `funcionalidad/base-alineacion` representa la etapa minima de alineacion del proyecto:

- estructura raiz coherente con el proyecto
- `docker-compose.yml` en la raiz
- `.env.example`
- `.gitignore`
- backend Spring Boot base en `vivero-backend/`
- eliminacion del contenido mezclado de dataset y archivos compilados versionados

Esta rama no incluye todavia:

- autenticacion completa
- configuracion de seguridad final
- modulos de negocio
- frontend
- puente de robot
- codigo del robot

## Estructura esperada en esta etapa

```text
.
|-- .env.example
|-- .gitignore
|-- docker-compose.yml
|-- README.md
|-- SAGA_FLOW.md
`-- vivero-backend/
    |-- Dockerfile
    |-- pom.xml
    |-- SAGA_FLOW.md
    `-- src/
```

## Ejecucion local

### Docker

```bash
docker compose up --build
```

### Compilacion del backend

```bash
cd vivero-backend
mvn -q -DskipTests compile
```

## Siguiente etapa

La siguiente rama en el orden historico es `funcionalidad/endurecimiento-auth`, donde se incorporan:

- `config/`
- `module/auth/`
- enums de dominio
- `data.sql`
- ajustes de seguridad y JWT
