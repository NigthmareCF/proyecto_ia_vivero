# ══════════════════════════════════════════════════════
# Dockerfile — vivero-backend
# Multi-stage build: ~200MB final image vs ~500MB single-stage
# ══════════════════════════════════════════════════════

# -- Stage 1: Build -----------------------------------
FROM maven:3.9.6-eclipse-temurin-17 AS builder

WORKDIR /build

# Copy pom.xml first to leverage Docker layer caching.
# If only source code changes, Maven won't re-download dependencies.
COPY pom.xml .
RUN mvn dependency:go-offline -B

COPY src ./src
RUN mvn clean package -DskipTests -B

# -- Stage 2: Runtime ---------------------------------
FROM eclipse-temurin:17-jre-jammy

WORKDIR /app

# Non-root user for security
RUN groupadd -r vivero && useradd -r -g vivero vivero

COPY --from=builder /build/target/*.jar app.jar

# Image storage directory (mounted as Docker volume)
RUN mkdir -p /app/images && chown -R vivero:vivero /app

USER vivero

EXPOSE 8080

ENV SPRING_PROFILES_ACTIVE=dev
ENV JAVA_OPTS="-Xms256m -Xmx512m"

# Docker will know when the backend is ready
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/api/actuator/health || exit 1

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
