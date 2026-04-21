# Google OAuth Backend Setup

## Estado actual

El backend ya acepta login con Google por `idToken` usando:

- `POST /api/auth/google`

Body:

```json
{
  "idToken": "GOOGLE_ID_TOKEN"
}
```

Respuesta:

- `accessToken`
- `refreshToken`
- datos del usuario local

## Configuracion requerida

Variable de entorno:

```env
GOOGLE_CLIENT_ID=tu_google_web_client_id.apps.googleusercontent.com
```

## Comportamiento

- el backend valida el `idToken` contra el `GOOGLE_CLIENT_ID`
- exige que el email de Google venga verificado
- si el usuario ya existe por email, inicia sesion sobre ese usuario local
- si no existe, crea uno nuevo con:
  - `role = VIEWER`
  - password aleatoria interna
  - `active = true`

## Nota para frontend

El frontend debe obtener el `idToken` desde Google Identity Services y mandarlo al backend.

No se implementó en esta etapa:

- flujo redirect de Spring Security OAuth2
- login con Apple
- selección de rol durante alta social
