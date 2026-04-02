# SAGA FLOW - Module Users

## Proposito

El modulo `users` administra el catalogo de usuarios del sistema despues del login inicial.
Permite a un `ADMIN` listar, crear, actualizar, cambiar roles y eliminar usuarios sin mezclar esa logica con `auth`.

## Flujo principal

1. Un `ADMIN` autenticado invoca `/api/users`
2. `UserController` valida el request y delega a `UserService`
3. `UserServiceImpl` consulta o modifica `UserRepository`
4. Si hay conflicto de email o una operacion invalida sobre el propio usuario, se lanza `BusinessException`
5. La respuesta vuelve envuelta en `ApiResponse<T>`

## Reglas de negocio actuales

- solo `ADMIN` puede usar este modulo
- no se puede eliminar la propia cuenta autenticada
- no se puede desactivar la propia cuenta autenticada
- no se puede cambiar el propio rol desde este modulo
- el email debe ser unico
- la contrasena es obligatoria al crear y opcional al actualizar
