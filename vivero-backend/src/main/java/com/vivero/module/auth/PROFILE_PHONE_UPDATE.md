# Auth Profile Phone Update

## Resumen

- `RegisterRequestDto` acepta `phoneNumber`.
- `AuthResponseDto` devuelve `phoneNumber`.
- Existe `PUT /api/auth/me` para actualizar el `phoneNumber` del usuario autenticado.

## Compatibilidad

- `phoneNumber` es nullable.
- Los usuarios existentes siguen siendo validos aunque no lo tengan cargado.

## Endpoint

`PUT /api/auth/me`

Body:

```json
{
  "phoneNumber": "+50212345678"
}
```
