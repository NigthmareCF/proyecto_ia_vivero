# AgroTech Robot Pi

Runtime fisico del robot para Raspberry Pi 5 dentro del proyecto AgroTech Vivero.

## Estado del runtime

Este repositorio contiene el runtime vigente del robot, no la vision futura completa.

Implementado hoy:

- seguimiento de linea
- deteccion de obstaculos
- lectura de QR
- captura de observaciones
- heartbeat y observaciones al backend
- modos de control
- telemetria base
- IA local opcional

No implementado aun:

- captura lateral en movimiento sin detener el robot
- streaming real completo de tres camaras
- flujo concurrente final de camaras

## Arquitectura vigente

La referencia vigente es comunicacion desde la Raspberry Pi hacia la entrada Nginx del stack `release`, y de ahi al backend/frontend:

```text
Pi -> Nginx -> backend -> frontend
```

La configuracion vigente usa `BACKEND_BASE_URL` para HTTP y `BACKEND_WS_URL` para WebSocket. En la red local actual el stack `release` publica Nginx en `3000`, por lo que el robot debe apuntar a:

```text
BACKEND_BASE_URL=http://192.168.1.27:3000/api
BACKEND_WS_URL=ws://192.168.1.27:3000/api/ws/robot-stream
```

En VM o dominio publico, usar la misma ruta por Nginx sin exponer el backend directo:

```text
BACKEND_BASE_URL=https://dominio-o-ip/api
BACKEND_WS_URL=wss://dominio-o-ip/api/ws/robot-stream
```

`BRIDGE_URL` queda obsoleto para esta rama y no debe usarse para la operacion normal.

## Roles de camaras acordados

- `front`: stream de operacion, supervision manual y evidencia ante obstaculos
- `left`: QR lateral y evidencia de planta
- `right`: QR lateral y evidencia de planta

Mapeo local verificado en la Raspberry Pi:

```text
left  -> /dev/video0
right -> /dev/video2
front -> /dev/video4
```

## Requisitos previos en la Raspberry Pi

1. Raspberry Pi OS 64-bit instalado.
2. Docker y Docker Compose disponibles.
3. I2C habilitado si usas LCD.
4. Camaras detectadas por Linux.
5. GPIO y sensores cableados segun la documentacion de circuito.

## Pinout vigente

```text
L298N
  GPIO17 -> IN1
  GPIO27 -> IN2
  GPIO22 -> IN3
  GPIO23 -> IN4

HC-SR04
  GPIO5  -> TRIG
  GPIO6  <- ECHO con divisor 1k-2k obligatorio

IR obstaculos
  GPIO16 <- izquierdo
  GPIO20 <- derecho

Line follower
  GPIO13 <- LEFT
  GPIO19 <- CENTER
  GPIO26 <- RIGHT

LCD I2C
  GPIO2 <-> SDA
  GPIO3 <-> SCL

Indicadores
  GPIO21 -> buzzer
  GPIO12 -> LED verde
  GPIO24 -> LED amarillo
  GPIO25 -> LED rojo
```

## Instalacion

Consulta la guia rapida en [ROBOT_PI_INSTALACION_DOCKER.md](ROBOT_PI_INSTALACION_DOCKER.md).

## Flujo vigente

Consulta el flujo operativo vigente en [SAGA_FLOW.md](SAGA_FLOW.md).
