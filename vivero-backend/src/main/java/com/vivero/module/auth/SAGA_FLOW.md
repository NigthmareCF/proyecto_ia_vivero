# SAGA FLOW — Módulo Auth
## Versión 1.0 | Spring Boot 3.2 + JWT | Marzo 2026

---

## 1. Archivos del módulo

```
module/auth/
├── controller/
│   └── AuthController.java          — endpoints REST públicos y protegidos
├── service/
│   ├── AuthService.java             — interfaz del servicio
│   └── impl/
│       ├── AuthServiceImpl.java     — lógica de login, registro y refresh
│       └── CustomUserDetailsService.java — carga usuario de DB para Spring Security
├── repository/
│   └── UserRepository.java          — consultas JPA sobre tabla users
├── entity/
│   └── User.java                    — tabla users + implementa UserDetails
├── dto/
│   ├── LoginRequestDto.java         — entrada: email + password
│   ├── RegisterRequestDto.java      — entrada: datos del nuevo usuario
│   ├── RefreshTokenRequestDto.java  — entrada: refresh token
│   └── AuthResponseDto.java         — salida: tokens + datos del usuario
└── util/
    └── JwtUtil.java                 — generar, validar y leer tokens JWT

config/ (relacionado directamente con auth)
├── SecurityConfig.java              — reglas de acceso, CORS, BCrypt, filtros
├── JwtAuthFilter.java               — intercepta y valida token en cada request
├── AppProperties.java               — mapea app.* del application.yml
├── AsyncConfig.java                 — pool de hilos para notificaciones async
└── WebSocketConfig.java             — STOMP endpoints para robot y cámara
```

---

## 2. Flujo: Login

```
Cliente (frontend)
    │
    │  POST /api/auth/login
    │  Body: { email, password }
    ▼
AuthController.login()
    │  @Valid valida que email y password no estén vacíos
    │  Si falla validación → GlobalExceptionHandler → HTTP 400
    ▼
AuthServiceImpl.login()
    │
    ├── AuthenticationManager.authenticate(email, password)
    │       │
    │       ├── CustomUserDetailsService.loadUserByUsername(email)
    │       │       └── UserRepository.findByEmail(email)
    │       │               └── Si no existe → UsernameNotFoundException → HTTP 401
    │       │
    │       └── BCryptPasswordEncoder.matches(rawPassword, encodedPassword)
    │               └── Si no coincide → BadCredentialsException → HTTP 401
    │
    ├── UserRepository.findByEmail(email) → User entity
    │
    ├── JwtUtil.generateAccessToken(user)  → token con expiración 24h
    ├── JwtUtil.generateRefreshToken(user) → token con expiración 7 días
    │
    └── Retorna AuthResponseDto { accessToken, refreshToken, userId, fullName, email, role }
    │
    ▼
AuthController → HTTP 200
Body: ApiResponse { success: true, data: AuthResponseDto }
```

---

## 3. Flujo: Request autenticado (JwtAuthFilter)

```
Cliente envía cualquier request protegido
    │
    │  GET /api/plants
    │  Header: Authorization: Bearer eyJhbGc...
    ▼
JwtAuthFilter.doFilterInternal()
    │
    ├── Lee header Authorization
    │       └── Si no existe o no empieza con "Bearer " → continúa sin autenticar
    │
    ├── Extrae token (elimina "Bearer ")
    │
    ├── JwtUtil.extractEmail(token)
    │       └── Si el token está malformado → continúa sin autenticar → Spring devuelve 401
    │
    ├── CustomUserDetailsService.loadUserByUsername(email) → UserDetails
    │
    ├── JwtUtil.isTokenValid(token, userDetails)
    │       ├── Verifica que email del token == email del usuario
    │       └── Verifica que el token no esté expirado
    │
    ├── Si válido → SecurityContextHolder.setAuthentication(authToken)
    │       └── Spring Security permite el acceso al endpoint
    │
    └── Si inválido → continúa sin autenticar → Spring devuelve 401
```

---

## 4. Flujo: Registro de usuario nuevo

```
Admin autenticado
    │
    │  POST /api/auth/register
    │  Header: Authorization: Bearer <admin_token>
    │  Body: { firstName, lastName, email, password, role }
    ▼
JwtAuthFilter → valida token del admin
    │
    ▼
AuthController.register()
    │  @PreAuthorize("hasRole('ADMIN')") → si no es admin → HTTP 403
    │  @Valid → valida campos → si falla → HTTP 400
    ▼
AuthServiceImpl.register()
    │
    ├── UserRepository.existsByEmail(email)
    │       └── Si ya existe → BusinessException → HTTP 400 "EMAIL_ALREADY_EXISTS"
    │
    ├── BCryptPasswordEncoder.encode(rawPassword) → password encriptado
    │
    ├── User.builder() → construye entidad
    ├── UserRepository.save(user) → INSERT en tabla users
    │
    ├── JwtUtil.generateAccessToken(newUser)
    ├── JwtUtil.generateRefreshToken(newUser)
    │
    └── Retorna AuthResponseDto del usuario recién creado
    │
    ▼
AuthController → HTTP 201 Created
```

---

## 5. Flujo: Refresh de token

```
Cliente detecta que el accessToken expiró (HTTP 401 en cualquier request)
    │
    │  POST /api/auth/refresh
    │  Body: { refreshToken: "eyJhbGc..." }
    ▼
AuthController.refresh() — endpoint público, no necesita token en header
    │
    ▼
AuthServiceImpl.refresh()
    │
    ├── JwtUtil.extractEmail(refreshToken)
    │       └── Si malformado → BusinessException → HTTP 400
    │
    ├── JwtUtil.isTokenExpired(refreshToken)
    │       └── Si expiró → BusinessException → HTTP 400 "REFRESH_TOKEN_EXPIRED"
    │               → el usuario debe volver a hacer login
    │
    ├── UserRepository.findByEmail(email) → User
    │
    ├── JwtUtil.generateAccessToken(user) → nuevo accessToken
    │
    └── Retorna AuthResponseDto con nuevo accessToken + mismo refreshToken
    │
    ▼
HTTP 200 — cliente actualiza el accessToken almacenado y reintenta el request original
```

---

## 6. Estructura de un JWT generado

```
Header:  { "alg": "HS256" }
Payload: {
  "sub":  "admin@vivero.com",    ← email del usuario (subject)
  "role": "ROLE_ADMIN",          ← rol para @PreAuthorize
  "iat":  1710768000,            ← issued at (Unix timestamp)
  "exp":  1710854400             ← expiration (iat + 24h)
}
Signature: HMACSHA256(base64(header) + "." + base64(payload), SECRET_KEY)
```

---

## 7. Roles y acceso

| Endpoint              | ADMIN | OPERATOR | VIEWER | Público |
|-----------------------|-------|----------|--------|---------|
| POST /auth/login      |       |          |        | ✓       |
| POST /auth/refresh    |       |          |        | ✓       |
| POST /auth/register   | ✓     |          |        |         |
| GET  /auth/me         | ✓     | ✓        | ✓      |         |

---

## 8. Dependencias entre archivos

```
SecurityConfig
    ├── depende de → JwtAuthFilter
    ├── depende de → CustomUserDetailsService
    └── define → AuthenticationManager, PasswordEncoder, SecurityFilterChain

JwtAuthFilter
    ├── depende de → JwtUtil
    └── depende de → CustomUserDetailsService

AuthServiceImpl
    ├── depende de → UserRepository
    ├── depende de → PasswordEncoder  (bean de SecurityConfig)
    ├── depende de → AuthenticationManager (bean de SecurityConfig)
    └── depende de → JwtUtil

JwtUtil
    └── depende de → AppProperties (lee jwt.secret y jwt.expiration-ms)
```
