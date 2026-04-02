# SAGA FLOW - Module Plants

## Proposito

El modulo `plants` administra el catalogo base de plantas del vivero.
Centraliza el QR unico, la ubicacion, la descripcion y el estado actual visible en dashboard y reportes.

## Flujo principal

1. Un usuario autenticado consulta o administra `/api/plants`
2. `PlantController` valida el request y delega a `PlantService`
3. `PlantServiceImpl` consulta o modifica `PlantRepository`
4. Si el QR ya existe o la planta no existe, se lanza la excepcion correspondiente
5. La respuesta vuelve envuelta en `ApiResponse<T>`

## Reglas de negocio actuales

- `ADMIN`, `OPERATOR` y `VIEWER` pueden consultar plantas
- solo `ADMIN` y `OPERATOR` pueden crear o actualizar plantas
- solo `ADMIN` puede eliminar plantas
- el QR debe ser unico
- el estado actual de la planta se guarda directamente en la entidad
- las observaciones manuales detalladas se integraran despues con `patrols/observations`