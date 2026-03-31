# SAGA FLOW

## Alcance general

Esta rama solo prepara la base tecnica para el sistema completo.

## Flujo de construccion del proyecto

1. Alinear la estructura raiz del repositorio
2. Dejar un backend base compilable
3. Incorporar seguridad y autenticacion
4. Agregar modulos de negocio
5. Integrar frontend
6. Integrar puente de robot
7. Integrar robot Raspberry Pi

## Flujo arquitectonico esperado

```text
Usuario
  |
  v
Frontend
  |
  v
Backend
  |
  +--> Base de datos
  +--> Volumen de imagenes
  |
  v
Robot Bridge
  |
  v
Robot Pi
```

## Objetivo de esta etapa

`funcionalidad/base-alineacion` debe dejar:

- un punto de partida limpio
- una raiz consistente
- un backend base compilable
- una convencion clara para continuar las ramas siguientes
