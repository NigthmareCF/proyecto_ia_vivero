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
- IMU MPU6050 opcional en bus I2C dedicado

## Formato QR operativo

El runtime envia al backend el contenido del QR tal como lo detecta. Para operacion vigente, el QR de planta debe codificarse asi:

```text
PLA_<planta>_MA_<maceta>_<lado>
```

Donde:

- `<planta>` identifica el correlativo de planta dentro del bloque o bandeja
- `<maceta>` identifica la maceta o grupo fisico
- `<lado>` debe ser `D`, `I` u `O`

Ejemplo:

```text
PLA_07_MA_03_D
```

Eso permite al backend consolidar evidencia por grupo `PLA_07_MA_03` y asociar la causa observada al lado correcto.

No implementado aun:

- captura lateral en movimiento sin detener el robot
- streaming real completo de tres camaras
- flujo concurrente final de camaras

## Arquitectura vigente

La referencia actual ya no es `Pi -> bridge -> backend` como camino obligatorio. La direccion principal es:

```text
Pi -> backend -> frontend
```

La configuracion vigente usa `BACKEND_BASE_URL` para HTTP y `BACKEND_WS_URL` para WebSocket. El runtime conserva compatibilidad con `BRIDGE_URL` solo como fallback legado.

## Roles de camaras acordados

- `front`: stream de operacion, supervision manual y evidencia ante obstaculos
- `left`: QR lateral y evidencia de planta
- `right`: QR lateral y evidencia de planta

## Requisitos previos en la Raspberry Pi

1. Raspberry Pi OS 64-bit instalado.
2. Docker y Docker Compose disponibles.
3. I2C habilitado si usas LCD.
4. I2C adicional habilitado si usas la IMU.
5. Camaras detectadas por Linux.
6. GPIO y sensores cableados segun la documentacion de circuito.

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

IMU MPU6050
  SDA/SCL -> bus I2C dedicado configurado por IMU_I2C_BUS

Indicadores
  GPIO21 -> buzzer
  GPIO12 -> LED verde
  GPIO24 -> LED amarillo
  GPIO25 -> LED rojo
```

## Instalacion

Consulta la guia rapida en [ROBOT_PI_INSTALACION_DOCKER.md](./ROBOT_PI_INSTALACION_DOCKER.md).

## Flujo vigente

Consulta el flujo operativo vigente en [SAGA_FLOW.md](./SAGA_FLOW.md).
