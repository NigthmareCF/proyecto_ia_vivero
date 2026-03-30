# SAGA FLOW — Configuración
## Versión 1.0 | Spring Boot 3.2 | Marzo 2026

---

## 1. Archivos del módulo

```
config/
├── SecurityConfig.java     — cadena de filtros, CORS, BCrypt, rutas públicas/protegidas
├── JwtAuthFilter.java      — intercepta cada HTTP request y valida el token JWT
├── AppProperties.java      — mapea propiedades app.* de application.yml a clases Java
├── AsyncConfig.java        — pool de hilos dedicado para notificaciones @Async
└── WebSocketConfig.java    — broker STOMP para control del robot y stream de cámara
```

---

## 2. Orden de carga de Spring al iniciar

```
1. Spring Boot arranca
        │
        ▼
2. AppProperties carga propiedades del application.yml
   (jwt.secret, jwt.expiration-ms, storage.images-path, etc.)
        │
        ▼
3. CustomUserDetailsService se registra como bean
        │
        ▼
4. JwtUtil se registra como bean (depende de AppProperties)
        │
        ▼
5. JwtAuthFilter se registra como bean (depende de JwtUtil + CustomUserDetailsService)
        │
        ▼
6. SecurityConfig se construye:
   - Registra JwtAuthFilter en la cadena de filtros
   - Define PasswordEncoder (BCrypt factor 12)
   - Define AuthenticationManager con CustomUserDetailsService + BCrypt
   - Configura CORS
   - Configura rutas públicas y protegidas
        │
        ▼
7. WebSocketConfig registra el endpoint /ws con SockJS fallback
        │
        ▼
8. AsyncConfig registra el ThreadPoolTaskExecutor para notificaciones
        │
        ▼
9. Aplicación lista — escuchando en :8080
```

---

## 3. Flujo de una petición HTTP a través de los filtros

```
Petición HTTP entrante
    │
    ▼
CORS Filter (configurado en SecurityConfig)
    │  Agrega headers Access-Control-Allow-Origin
    │  Responde OPTIONS preflight sin pasar al filtro JWT
    │
    ▼
JwtAuthFilter
    │  Lee Authorization: Bearer <token>
    │  Extrae email, carga usuario, valida token
    │  Si válido → registra autenticación en SecurityContextHolder
    │
    ▼
Spring Security Authorization
    │  Verifica si la ruta requiere autenticación
    │  Si requiere rol → verifica getAuthorities() del usuario
    │  Si no tiene permiso → HTTP 403
    │
    ▼
DispatcherServlet → Router → Controller → Service → Repository
```

---

## 4. Configuración de rutas (SecurityConfig)

```
Rutas PÚBLICAS (sin token requerido):
  POST  /api/auth/login
  POST  /api/auth/refresh
  GET   /api/actuator/health
  GET   /api/actuator/info
  WS    /api/ws/**

Rutas PROTEGIDAS (token JWT requerido):
  Cualquier otra ruta — Spring verifica el SecurityContext

Control de roles por endpoint:
  @PreAuthorize("hasRole('ADMIN')")    → solo ADMIN
  @PreAuthorize("hasRole('OPERATOR')") → solo OPERATOR
  @PreAuthorize("hasAnyRole('ADMIN','OPERATOR')") → ambos
  (definido en cada Controller, no en SecurityConfig)
```

---

## 5. WebSocket — canales disponibles

```
Conexión:
  Cliente conecta a: ws://localhost:8080/api/ws

Topics a los que el cliente puede suscribirse:
  /topic/patrol/updates     ← actualizaciones de estado durante patrullaje
  /topic/robot/stream       ← frames de cámara en tiempo real
  /topic/robot/status       ← cambios de modo y estado del robot

Destinos a los que el cliente puede publicar:
  /app/robot/control        ← comandos de control manual (dirección + velocidad)
```

---

## 6. Pool de hilos async (AsyncConfig)

```
Bean: notificationExecutor

Configuración:
  corePoolSize  = 4   → siempre activos
  maxPoolSize   = 10  → máximo en picos de carga
  queueCapacity = 50  → cola si todos los hilos están ocupados
  threadPrefix  = "notification-"

Uso:
  @Async("notificationExecutor")
  public void sendEmail(...) { ... }   ← no bloquea el thread del request REST
```
