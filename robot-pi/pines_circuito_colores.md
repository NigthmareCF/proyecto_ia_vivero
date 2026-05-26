# PINES, CIRCUITOS Y COLORES
## Robot AgroTech Vivero — Especificación técnica completa v4.0

> **Versión actual**  
> Este documento unifica conectividad de GPIO, polaridades de componentes, esquemas de energía y especificación de hardware del robot agrícola autónomo.  
> Sirve como guía única para armado, diagnóstico y mantenimiento.

---

# 1. TABLA MAESTRA: CÓDIGO DE COLORES DE JUMPERS (Raspberry Pi 5)

## Mapeo de colores → GPIO y funciones

| Color Jumper | Función | Pines Físicos |
|---|---|---|
| **Negro** | GND (Tierra) | 6, 9, 14, 20, 25, 30, 34, 39 |
| **Rojo** | +5V (Poder) | 2, 4 |
| **Naranja** | +3.3V (Poder) | 1, 17 |
| **Verde** | GPIO 2, 3 (I2C) | 3, 5 |
| **Blanco** | GPIO 14, 15 (UART) | 8, 10 |
| **Gris** | DNC (Reservados) | 27, 28 |
| **Amarillo** | GPIO 4, 17, 18, 27, 22, 23, 24 | 7, 11, 12, 13, 15, 16, 18 |
| **Café** | GPIO 7, 8, 9, 10, 11 | 26, 24, 21, 19, 23 |
| **Morado** | GPIO 25, 5 | 22, 29 |
| **Azul** | GPIO 6, 12, 13, 19, 16, 26, 20, 21 | 31, 32, 33, 35, 36, 37, 38, 40 |

---

# 2. ARQUITECTURA ELÉCTRICA GENERAL

El robot se divide en **6 subsistemas principales**:

## 2.1 Procesamiento
- Raspberry Pi 5 (4GB o 8GB)
- microSD 64GB
- 3 cámaras USB 1080p

## 2.2 Movimiento (L298N + Motores DC)
- Driver L298N con control PWM (GPIO18/ENA, GPIO25/ENB)
- 4 motores DC con reductora 12V
- Velocidad: 3 perfiles (Lento 40%, Medio 65%, Rápido 85%) + perfil admin personalizado

## 2.3 Sensores de navegación y detección

### Seguimiento de línea
- **TCRT5000 (centro, 4 pines):** VCC, GND, A0 (analógico), D0 (digital GPIO19)
- **MH-B izquierdo (3 pines):** VCC, GND, OUT → GPIO13
- **MH-B derecho (3 pines):** VCC, GND, OUT → GPIO16
- Configuración: 3 sensores IR digitales en línea (izq-centro-der) para seguimiento de trayectoria

### Detección de obstáculos (trasero)
- **Trasero izquierdo:** 1× sensor IR proximidad (3 pines: VCC, GND, OUT) → GPIO8
- **Trasero derecho:** 1× sensor IR proximidad (3 pines: VCC, GND, OUT) → GPIO9
- Ubicación: Parte superior como "luces traseras"
- Función: Detección de obstáculos y proximidad durante retroceso

### Ultrasonido (frente)
- **HC-SR04:** 1× sensor ultrasónico (4 pines: VCC, TRIG, ECHO, GND)
- Ubicación: Centro frontal
- Función: Detección principal de obstáculos

## 2.4 Interfaz local
- Pantalla LCD 16x2 con módulo I2C (4 pines: GND, VCC, SDA, SCL)
- Buzzer activo (2 pines: positivo, GND)
- 4× LEDs indicadores (colores con resistencias 220Ω):
  - **Verde** (GPIO12) → sano
  - **Amarillo** (GPIO24) → atención
  - **Rojo** (GPIO26) → peligro
  - **Azul** (GPIO20) → heartbeat

## 2.5 Energía (Sistema triple)

### Sistema A: Procesamiento e I/O (Powerbank Li-ion → Pi 5)
- **Pack:** 6× 18650 (3.3V, 4800mAh c/u) en configuración **3S2P**
  - Voltaje nominal: 11.1V nominal, ~12.6V máximo
  - Capacidad: 9600mAh
- **BMS:** 3S 40A
  - Entradas: 0V (GND), 4.2V (celda 1), 8.4V (celda 2), 12.6V (celda 3)
  - Salidas: (+), (−) hacia step-down
  - Protección: sobrecarga, desbalance, cortocircuito
- **Step-Down:** XL4015 configurado a **5.1V** / 5A
  - Entrada: 12.6V desde BMS
  - Salida: 5.1V → Pi 5 (vía USB-C macho a hembra integrada en Pi)
  - **Ventilador 12V:** 1× conectado a entrada del step-down (12.6V BMS) — funciona durante operación

### Sistema B: Carga del powerbank (Step-Up + Enfriamiento de carga)
- **Step-Up:** XL6009E1 configurado a **12.6V** / 30W
  - Entrada: 9-24V desde cargador externo
  - Salida: 12.6V → BMS para recarga equilibrada
  - **Ventilador 12V:** 1× conectado a salida del step-up (12.6V) — funciona durante carga
  - **Uso:** Solo activo mientras se carga el powerbank; evita sobrecalentamiento

### Sistema C: Enfriamiento distribuido (Agrupador AA → Ventiladores 5V)
- **Pack AA:** 1× agrupador de 4 baterías AA recargables (1.2V, 1300mAh c/u = 4.8V total)
- **Regulador 5V integrado:** Convierte 4.8V → ~5V estable
- **Distribución de ventiladores 5V:**
  - 1× ventilador 5V → Pi 5 (enfriador disipador)
  - 2× ventiladores 5V → L298N (evitar sobrecalentamiento del driver motor)
- **Función:** Sistema independiente del powerbank; no consume de la batería principal
- **Ventaja:** Enfriamiento continuo sin impactar autonomía
- **Nota:** 2 agrupadores disponibles; uno en uso, uno como respaldo/repuesto

---

# 3. MAPA COMPLETO DE PINES — Raspberry Pi 5

## 3.1 Vista de 40 pines (esquemático)

```text
    RASPBERRY PI 5 — VISTA DE ARRIBA (40 pines, doble fila)

    LADO IZQUIERDO (ODD)         │        LADO DERECHO (EVEN)
    ═════════════════════════════╪═════════════════════════════════

    +3.3V  (Poder)         [1]   ║  [2]   +5V           → LCD, sensores
    GPIO2  (SDA/I2C)       [3]   ║  [4]   +5V           → LCD, sensores
    GPIO3  (SCL/I2C)       [5]   ║  [6]   GND           → COMÚN
    GPIO4                  [7]   ║  [8]   GPIO8         → IR trasero izq
    GND                    [9]   ║  [10]  GPIO9         → IR trasero der
    GPIO17 (L298N IN1)     [11]  ║  [12]  GPIO18/PWM    → ENA (velocidad izq)
    GPIO27 (L298N IN2)     [13]  ║  [14]  GND           → COMÚN
    GPIO22 (L298N IN3)     [15]  ║  [16]  GPIO24        → LED amarillo
    GPIO23 (L298N IN4)     [17]  ║  [18]  GPIO25        → ENB (velocidad der)
    GPIO10 (SPI)           [19]  ║  [20]  GND           → COMÚN
    GPIO9  (SPI)           [21]  ║  [22]  GPIO11/SPI    → (reservado)
    GPIO11 (SPI)           [23]  ║  [24]  GPIO8/SPI     → (reservado)
    GND                    [25]  ║  [26]  GPIO7/SPI     → (reservado)
    GPIO0  (ID EEPROM)     [27]  ║  [28]  GPIO1 (ID)    → (reservado)
    GPIO5  (HC-SR04 TRIG)  [29]  ║  [30]  GND           → COMÚN
    GPIO6  (HC-SR04 ECHO)  [31]  ║  [32]  GPIO12        → LED verde
    GPIO13 (Line LEFT)     [33]  ║  [34]  GND           → COMÚN
    GPIO19 (Line CENTER)   [35]  ║  [36]  GPIO16        → Line RIGHT (MH-B der)
    GPIO26 (LED Rojo)      [37]  ║  [38]  GPIO20        → LED azul
    GND                    [39]  ║  [40]  GPIO21        → Buzzer activo

    ═════════════════════════════════════════════════════════════════
```

## 3.2 Asignación de GPIO por función

### Alimentación
- **Pin 2, 4:** +5V (desde step-down)
- **Pin 6, 9, 14, 20, 25, 30, 34, 39:** GND (tierra común)

### Control de motores (L298N)
- **GPIO17 (pin 11):** IN1 → Motor izquierdo adelante
- **GPIO27 (pin 13):** IN2 → Motor izquierdo atrás
- **GPIO22 (pin 15):** IN3 → Motor derecho adelante
- **GPIO23 (pin 17):** IN4 → Motor derecho atrás
- **GPIO18 (pin 12):** ENA (PWM) → Control velocidad motores izquierdos
- **GPIO25 (pin 18):** ENB (PWM) → Control velocidad motores derechos

### Sensores de línea (seguimiento)
- **GPIO13 (pin 33):** Salida MH-B izquierdo
- **GPIO19 (pin 35):** Salida TCRT5000 central
- **GPIO16 (pin 36):** Salida MH-B derecho

### Sensores IR de obstáculos (traseros)
- **GPIO8 (pin 24):** Salida IR trasero izquierdo
- **GPIO9 (pin 21):** Salida IR trasero derecho
- Función: Detección de proximidad/obstáculos traseros

### Pantalla LCD I2C
- **GPIO2 (pin 3, SDA):** Serial Data
- **GPIO3 (pin 5, SCL):** Serial Clock
- **Pin 2 o 4:** +5V
- **GND:** Tierra común

### Buzzer y LEDs
- **GPIO21 (pin 40):** Buzzer activo (positivo)
- **GPIO12 (pin 32):** LED verde — R220Ω a GND (sano)
- **GPIO24 (pin 16):** LED amarillo — R220Ω a GND (atención)
- **GPIO26 (pin 37):** LED rojo — R220Ω a GND (peligro)
- **GPIO20 (pin 38):** LED azul — R220Ω a GND (heartbeat)
- **GND común:** Todos los cátodos

### Cámaras USB
- **USB1 (superior izquierdo):** Cámara frontal
- **USB2 (superior derecho):** Cámara lateral izquierda
- **USB3 (inferior izquierdo):** Cámara lateral derecha

---

# 4. ESQUEMAS DE CIRCUITOS POR SUBSISTEMA

## 4.1 Control de motores L298N (PWM habilitado)

```text
RASPBERRY PI 5                          L298N                    MOTORES
───────────────                         ─────                    ────────

GPIO17  [IN1] ──────────────────────►  IN1
GPIO27  [IN2] ──────────────────────►  IN2    OUT1 ──────────► Motor IZQ-A
GPIO22  [IN3] ──────────────────────►  IN3    OUT2 ──────────► Motor IZQ-B
GPIO23  [IN4] ──────────────────────►  IN4
                                                OUT3 ──────────► Motor DER-A
GPIO18  [ENA] ──┐ PWM (0-255)          OUT4 ──────────► Motor DER-B
GPIO25  [ENB] ──┤ Control velocidad
                                    
Batería 12V ────────────────────────►  +12V
            ────────────────────────►  GND        (4 motores → ~3-4A)
            
GND (común) ────────────────────────►  GND

VELOCIDADES (ajustes PWM):
  - Lento:    40% (102/255)
  - Medio:    65% (166/255)
  - Rápido:   85% (217/255)
  - Admin:    personalizado (0-255)
```

## 4.2 Sensor ultrasónico HC-SR04 (con divisor obligatorio)

```text
RASPBERRY PI 5           HC-SR04              DIVISOR DE VOLTAJE
───────────────          ───────              ──────────────────

GPIO5 [TRIG] ──────────► TRIG    
                        
GPIO6 [ECHO] ◄───┬──── ECHO (5V)
                │
           [1kΩ]│
                ├────► GPIO6 (entrada)
               [2kΩ]
                │
               GND     
               
+5V (step-down) ──────► VCC

GND (común) ───────────► GND

VOLTAJE SEGURO EN GPIO6:
  Vout = 5V × (2kΩ / 3kΩ) = 3.33V ✓ SEGURO
```

## 4.3 Sensor ultrasónico (HC-SR04)

```text
RASPBERRY PI 5                           HC-SR04
───────────────                          ────────

GPIO5 [TRIG] ◄─── Pin 1 (Trigger 3.3V)
                        
GPIO6 [ECHO] ◄─────── Pin 2 (Echo 5V)
        ▲
        │ DIVISOR DE VOLTAJE (OBLIGATORIO)
        │ Entrada 5V → Salida 3.3V GPIO6
        │
    [1kΩ]│
        ├────► GPIO6 (entrada 3.3V)
       [2kΩ]
        │
       GND     
               
+5V (step-down) ◄─── Pin 3 (VCC)
GND (común) ◄─────── Pin 4 (GND)

VOLTAJE SEGURO EN GPIO6:
  Vout = 5V × (2kΩ / 3kΩ) = 3.33V ✓ SEGURO

FUNCIÓN: Detección principal de obstáculos frontal
  - Rango: 2cm a 400cm
  - Resolución: ~0.3cm
```

## 4.4 Sensores IR de obstáculos traseros

```text
IR IZQUIERDO TRASERO                    IR DERECHO TRASERO
(Ubicación: superior lateral izq)       (Ubicación: superior lateral der)
────────────────────────────────        ───────────────────────────────

  VCC ──┬──────► +5V                     VCC ──┬──────► +5V
  GND ──┤──────► GND                     GND ──┤──────► GND
  OUT ──┴──────► GPIO8                  OUT ──┴──────► GPIO9

DISPOSICIÓN FÍSICA:
  - Ubicados en parte superior trasera, simulando "luces traseras"
  - Uno a cada lateral para cobertura trasera simétrica
  
FUNCIÓN: Detección de proximidad/obstáculos durante retroceso
  - Previene colisiones traseras
  - Actúa como sensor de proximidad general trasero
  - Rango típico: 2cm a 30cm (según modelo IR)

LÓGICA: 1 = obstáculo detectado, 0 = sin obstáculo
```

## 4.5 Seguidor de línea (TCRT5000 + 2× MH-B)

```text
TCRT5000 (central, 4 pines)              MH-B IZQ (lateral, 3 pines)
─────────────────────────────            ──────────────────────────

VCC ────────────► +5V                    VCC ────────────► +5V
GND ────────────► GND                    GND ────────────► GND
A0 (analógico)──► (no usado en digital)  OUT ────────────► GPIO13
D0 (digital) ───► GPIO19 (CENTER)

MH-B DER (lateral, 3 pines)
──────────────────────────

VCC ────────────► +5V
GND ────────────► GND
OUT ────────────► GPIO16

CONFIGURACIÓN (En línea, izq-centro-der):
    [MH-B IZQ]     [TCRT5000]     [MH-B DER]
    GPIO13         GPIO19         GPIO16
       │              │              │
       └──────────────┬──────────────┘
               Seguimiento de línea

LÓGICA: 1 = línea negra detectada, 0 = sin línea

PATRÓN NORMAL EN LÍNEA NEGRA:
  GPIO13 (izq)  = 1
  GPIO19 (centro) = 1  ← Principal
  GPIO16 (der)  = 1

CORRECCIONES DE TRAYECTORIA:
  Si solo GPIO13 = 1 → desviarse a derecha
  Si solo GPIO19 = 1 → recto (centrado)
  Si solo GPIO16 = 1 → desviarse a izquierda
```

## 4.5 Pantalla LCD I2C

```text
RASPBERRY PI 5              LCD 16x2 + Módulo I2C
───────────────             ────────────────────

GPIO2 [SDA] ◄──────────────► SDA (pin 3 del módulo)
GPIO3 [SCL] ◄──────────────► SCL (pin 4 del módulo)
+5V ──────────────────────► VCC (pin 2)
GND ──────────────────────► GND (pin 1)

DIRECCIÓN I2C (típica):
  0x27 o 0x3F (verificar con: i2cdetect -y 1)

DATOS MOSTRADOS:
  - Estado del robot (AUTONOMO/MANUAL)
  - Maceta actual (#)
  - Diagnóstico del planta (sano/atención/peligro)
  - Resumen de patrullaje
```

## 4.6 Buzzer y LEDs

```text
                    BUZZER ACTIVO        LEDs INDICADORES
                    ───────────────      ─────────────────

GPIO21 ────────────► Positivo            GPIO12 ──[220Ω]──► Ánodo (LED verde)
                                         GPIO24 ──[220Ω]──► Ánodo (LED amarillo)
GND ───────────────► Negativo            GPIO26 ──[220Ω]──► Ánodo (LED rojo)
                                         GPIO20 ──[220Ω]──► Ánodo (LED azul)
                                         
                                         GND ───────────────► Cátodo (todos)

ESTADOS DEL ROBOT:
  Verde   (GPIO12) → Sistema sano, funcionando normal
  Amarillo(GPIO24) → Atención, revisar diagnóstico
  Rojo    (GPIO26) → Peligro, detener operación
  Azul    (GPIO20) → Heartbeat (parpadeo de vida)
```

---

# 5. ESPECIFICACIONES DE POLARIDAD POR COMPONENTE

## 5.1 Batería principal (Powerbank Li-ion 3S)

```text
CONECTOR DE SALIDA (BMS → Step-Down):

(+) Rojo   → Entrada +V del step-down
(−) Negro  → Entrada GND del step-down

VOLTAJE:
  - Sin carga: ~9.9V (con descarga leve)
  - Nominal: ~11.1V
  - Máximo: ~12.6V (12.6V nominal en celda llena)

⚠️ CRÍTICO: NUNCA invertir — cortocircuito instantáneo
```

## 5.2 Step-Down XL4015 (entrada 0-12.6V → salida 5.1V)

```text
ENTRADA (desde BMS):
  IN+ (rojo) ◄─── +12.6V máximo del BMS
  IN− (negro) ◄── GND común

SALIDA (hacia Pi 5):
  OUT+ (rojo) ───► +5.1V (ajustado con potenciómetro)
  OUT− (negro) ──► GND común

PROCEDIMIENTO INICIAL:
  1. Conecta entrada sin cargar salida
  2. Ajusta potenciómetro hasta leer 5.1V ±0.1V con multímetro
  3. Luego conecta Pi 5 y sensores
  
⚠️ Si salida > 5.5V → Pi 5 se daña. Ajusta cuidadosamente.
```

## 5.3 Step-Up XL6009E1 (entrada 9-24V → salida 12.6V)

```text
ENTRADA (fuente externa):
  IN+ ◄─── +9 a +24V desde cargador externo
  IN− ◄─── GND

SALIDA (hacia BMS):
  OUT+ ───► +12.6V (ajustado para cargar 3S en paralelo)
  OUT− ───► GND

FUNCIÓN: Recarga rápida del pack 3S desde fuente fija
  - Permite cargar el robot sin desarmarlo
  - Garantiza 12.6V para balance en celdas

⚠️ Ajusta cuidadosamente a 12.6V exacto (no subpasar, daña BMS)
```

## 5.4 LCD 16x2 I2C

```text
PIN 1 (GND)   → Negro (tierra común)
PIN 2 (VCC)   → Rojo (+5V desde step-down)
PIN 3 (SDA)   → Verde (GPIO2)
PIN 4 (SCL)   → Azul (GPIO3)

⚠️ CRÍTICO: Invertir GND/VCC daña el LCD y módulo I2C
```

## 5.5 LEDs (Verde, Amarillo, Rojo, Azul)

```text
PATA LARGA (ánodo +)   → GPIO (a través de R220Ω)
PATA CORTA (cátodo −)  → GND común

ESPECIFICACIONES:
  - Tensión directa: 1.8-2.2V (rojo/amarillo), 2.5-3V (verde/azul)
  - Corriente típica: 20mA máx
  - Corriente recomendada: 5-10mA (con R220Ω)

ASIGNACIÓN DE PINES:
  - GPIO12 (pin 32) → LED verde (2 unidades)
  - GPIO24 (pin 16) → LED amarillo (2 unidades)
  - GPIO26 (pin 37) → LED rojo (2 unidades)
  - GPIO20 (pin 38) → LED azul (4 unidades)


CÁLCULO DE RESISTENCIA:
  R = (Vgpio − Vled) / I
  R = (3.3V − 2.0V) / 0.020A = 65Ω
  → Usar R220Ω (conservador, más seguro)
```

## 5.6 Buzzer activo

```text
PATA ROJA (+)   → GPIO21
PATA NEGRA (−)  → GND común

CARACTERÍSTICAS:
  - Voltaje: 3.3V (compatible con GPIO)
  - Frecuencia: fija (típicamente 2-3kHz)
  - Corriente: ~10-15mA
  
⚠️ Debe ser ACTIVO (con oscilador interno), no pasivo
```

## 5.7 HC-SR04 ultrasónico

```text
VCC  → +5V (desde step-down)
GND  → GND común
TRIG → GPIO5 (envía pulso 3.3V)
ECHO → GPIO6 (recibe pulso 5V → REQUIERE DIVISOR)

DIVISOR ECHO OBLIGATORIO:
  ECHO (5V) ──[1kΩ]──┬──► GPIO6 (3.3V)
                    │
                   [2kΩ]
                    │
                   GND
                   
Voltaje en GPIO6: 5V × (2kΩ / 3kΩ) = 3.33V ✓
```

## 5.8 Sensores IR

```text
VCC  → +5V
GND  → GND común
OUT  → GPIO (16, 20, 14, 15 según posición)

SALIDA: Digital (0 = no detecta, 1 = detecta)

⚠️ Invertir VCC/GND no daña, solo no funciona
```

## 5.9 Motores DC con L298N

```text
MOTOR A (cable rojo) → OUT1 o OUT2 (intercambiable)
MOTOR B (cable negro) → OUT2 o OUT1

Voltaje: 12V (nominal)
Corriente: 200-800mA (sin carga a máxima carga)
Sentido: Invertible en hardware (intercambiando cables)

⚠️ Con 4 motores simultáneos: ~3-4A total
⚠️ L298N se protege con fusible interno (típicamente 2A por salida)
```

---

# 6. MATRIZ RESUMIDA DE POLARIDADES

```text
COMPONENTE              CRÍTICO?    SI SE INVIERTE
════════════════════════════════════════════════════════════════════
Powerbank BMS           ✓✓ FATAL    Cortocircuito/fuego
Step-Down entrada       ✓ ALTO      No funciona / lento
Step-Down salida        ✓✓ FATAL    Daña Pi 5
Step-Up entrada         ✓ ALTO      No funciona
LCD VCC/GND             ✓ ALTO      LCD/I2C dañados
LED (Á/C)               ✗ MENOR     No enciende (sin daño)
Buzzer (±)              ✗ MENOR     No suena
HC-SR04 VCC/GND         ✓ ALTO      No funciona
HC-SR04 ECHO            ✓✓ CRÍTICO  Daña GPIO6 sin divisor
HC-SR04 TRIG            ✗ TRIVIAL   No funciona
Motor DC (A/B)          ✗ TRIVIAL   Gira en sentido opuesto
IR sensor VCC/GND       ✗ MENOR     No detecta
════════════════════════════════════════════════════════════════════

✓✓ FATAL     = Detiene robot o lo daña permanentemente
✓ ALTO       = No funciona el subsistema, pero no daña
✓ CRÍTICO    = Daña Pi 5 si no se corrige
✗ MENOR      = Funciona pero de forma inesperada
✗ TRIVIAL    = Sin impacto o fácilmente reversible
```

---

# 7. SISTEMA DE ENERGÍA DETALLADO

## 7.1 Diagrama de flujo energético

```text
┌─────────────────────────────────────────────────────────────────┐
│                  ROBOT AGROTECNOLOGÍA VIVERO                    │
└─────────────────────────────────────────────────────────────────┘

OPERACIÓN NORMAL (Robot activo)
═════════════════════════════════════════════════════════════════

    POWERBANK 3S2P (11.1V nominal)
    6× 18650 4800mAh c/u
         │
         ▼
    ┌──────────────┐
    │ BMS 3S 40A   │ ◄─── Protección y balance
    │ Salida 12.6V │
    └──────┬───────┘
           │
      ┌────┴─────────────────────────┐
      │                              │
      ▼                              ▼
  ┌─────────────┐            ┌──────────────────┐
  │ STEP-DOWN   │            │ Ventilador 12V   │
  │ XL4015      │            │ (Enfriamiento    │
  │ Entrada:    │            │  operación)      │
  │ 12.6V       │            │                  │
  │ Salida:     │            └──────────────────┘
  │ 5.1V / 5A   │
  └──────┬──────┘
         │
    ┌────┴────────────────────────────────────┐
    │                                         │
    ▼                                         ▼
┌─────────────────┐              ┌─────────────────────┐
│  RASPBERRY PI 5 │              │ Sensores / LCD      │
│  (vía USB-C)    │              │ (5V)                │
│  5.1V           │              │                     │
└─────────────────┘              └─────────────────────┘


CARGA DEL POWERBANK (Robot desconectado)
════════════════════════════════════════════════════════════════

    Cargador externo
    9-24V DC
         │
         ▼
    ┌──────────────┐
    │ STEP-UP      │
    │ XL6009E1     │
    │ Entrada:     │
    │ 9-24V        │
    │ Salida:      │
    │ 12.6V        │
    └──────┬───────┘
           │
      ┌────┴──────────────────┐
      │                       │
      ▼                       ▼
  ┌──────────┐        ┌─────────────────┐
  │ BMS 3S   │        │ Ventilador 12V  │
  │ (carga)  │        │ (Enfriamiento   │
  │ 12.6V    │        │  del BMS)       │
  └──────────┘        └─────────────────┘


SISTEMA INDEPENDIENTE DE ENFRIAMIENTO (Siempre activo)
═══════════════════════════════════════════════════════

    Agrupador AA
    4× 1.2V (4.8V total)
         │
         ▼
    ┌──────────────┐
    │ Regulador 5V │
    │ ~4.8V → 5V   │
    └──────┬───────┘
           │
    ┌──────┴────────────────────┐
    │                           │
    ▼                           ▼
  1× Fan 5V            2× Fans 5V L298N
  (Pi 5 disipador)     (Motor driver)
```

## 7.2 Cálculos de consumo (estimado)

```text
DISPOSITIVO                 VOLTAJE    CORRIENTE    TIEMPO APROX
════════════════════════════════════════════════════════════════════
Raspberry Pi 5              5.1V       800mA        Continuo
HC-SR04                     5V         15mA         Activo
LCD 16x2 I2C                5V         40mA         Continuo
Buzzer                      3.3V       10mA         Picos
LEDs (4 total)              3.3V       20mA         Según estado
Sensores IR (4 total)       5V         60mA         Continuo
Ventilador 5V (1)           5V         200mA        Continuo/variable
Ventiladores 12V (2)        12V        600mA        Continuo/variable
Motores DC (4)              12V        3000mA       Bajo carga

CONSUMO MÁXIMO SIMULTÁNEO:
  - Sin motores: ~1.5A (Pi 5 + sensores + ventiladores)
  - Con motores: ~5-6A (cuando motores a máxima velocidad + ventiladores)

AUTONOMÍA (pack 3S):
  Pack: 9600mAh
  Consumo promedio: 2-3A
  Tiempo estimado: 3-5 horas en operación continua
  
  Con ventiladores activos continuamente: ~3 horas
  Con ventiladores modulados: ~5 horas

CARGA DEL POWERBANK (via XL6009E1 a 12.6V):
  Entrada: 1-2A desde fuente 12-24V
  Tiempo carga: ~5-8 horas (6 × 4800mAh = 28800 coulombs ÷ 1.5A)

SISTEMA DE ENFRIAMIENTO (Agrupador AA + 3× ventiladores 5V):
  Pack AA: 4× 1.2V 1300mAh = 4.8V total
  Autonomía ventiladores: ~8-10 horas continuo (sin carga Pi/motores)
  Función: Independiente del powerbank; solo para enfriamiento
  Ventaja: Sistema de calor no comparte batería con procesamiento/movimiento
```

## 7.3 TABLA MAESTRA: Conexión de componentes a módulos de energía

| COMPONENTE | VOLTAJE REQUERIDO | CONECTADO A | NOTAS |
|---|---|---|---|
| **Procesamiento** | | | |
| Raspberry Pi 5 | 5.1V | Step-Down XL4015 (vía USB-C macho) | Alimentación principal |
| microSD + USB cams | 5V | Pi 5 (puertos integrados) | A través de Pi 5 |
| **Sensores digitales/I2C** | | | |
| HC-SR04 (VCC) | 5V | Step-Down 5.1V | Entrada principal |
| HC-SR04 (GND) | GND | Tierra común (BMS) | Referencia común |
| TCRT5000 (VCC) | 5V | Step-Down 5.1V | Línea izq/centro/der |
| MH-B izq/der (VCC) | 5V | Step-Down 5.1V | Seguidores de línea |
| IR trasero izq/der (VCC) | 5V | Step-Down 5.1V | Obstáculos traseros |
| LCD 16x2 I2C (VCC) | 5V | Step-Down 5.1V | Módulo con integrador |
| LCD 16x2 I2C (SDA/SCL) | 3.3V | GPIO2, GPIO3 (Pi 5) | Comunicación I2C |
| **Indicadores locales** | | | |
| LEDs (4 total) | 3.3V | GPIO 12/24/26/20 (Pi 5) | Con R220Ω a GND |
| Buzzer activo | 3.3V | GPIO21 (Pi 5) | Sonido de alerta |
| **Control de motores** | | | |
| L298N (GND) | GND | Tierra común (BMS) | Referencia común |
| L298N (IN1/2/3/4) | 3.3V | GPIO 17/27/22/23 (Pi 5) | Control lógica |
| L298N (ENA/ENB) | 3.3V PWM | GPIO 18/25 (Pi 5) | Control velocidad |
| Motores DC (alimentación) | 12V | BMS 12.6V directamente | Máxima corriente |
| **Enfriamiento activo** | | | |
| Ventilador 12V (entrada) | 12V | BMS 12.6V (salida) | Durante operación robot |
| Ventilador 12V (carga) | 12V | Step-Up 12.6V (salida) | Durante carga del BMS |
| Ventiladores 5V (3 unidades) | 5V | Agrupador AA 4.8V + regulador | Independientes del powerbank |
|  |  | • 1× Pi 5 disipador |  |
|  |  | • 2× L298N driver |  |

---

# 8. INSTRUCCIONES DE MONTAJE ORDENADO

## Paso 1: Preparación y verificación

```
□ Verificar BMS sin daños (sin fracturas, pines intactos)
□ Cargar 6 celdas 18650 individualmente a 4.2V c/u
□ Verificar voltaje de cada celda con multímetro (4.1-4.2V)
□ Conectar celdas en configuración 3S2P respetando polaridad
□ Medir voltaje total: ~12.6V (máximo)
```

## Paso 2: Montaje de energía

```
□ Conectar BMS a pack (0V, 4.2V, 8.4V, 12.6V en orden)
□ Conectar salida BMS al Step-Down entrada
□ Conectar salida Step-Down al +5V/GND de Pi 5
□ Ajustar Step-Down a 5.1V (SIN CARGAR Pi 5)
□ Verificar estabilidad 10 minutos
□ Conectar Pi 5
```

## Paso 3: Control de motores

```
□ Conectar GPIO17, 27, 22, 23 al L298N (IN1-4)
□ Conectar GPIO18 al ENA (PWM izquierdo)
□ Conectar GPIO25 al ENB (PWM derecho)
□ Conectar motores a OUT1-4 (revisar sentido de giro)
□ Probar en baja velocidad (40% PWM)
```

## Paso 4: Sensores de navegación

```
□ HC-SR04: TRIG a GPIO5, ECHO a GPIO6 (CON DIVISOR 1k-2k)
□ TCRT5000: D0 a GPIO19 (line center)
□ MH-B izq: OUT a GPIO13 (line left)
□ MH-B der: OUT a GPIO16 (line right)
```

## Paso 5: Sensores de seguimiento de línea

```
□ TCRT5000 (centro): D0 a GPIO19
□ MH-B izquierdo: OUT a GPIO13
□ MH-B derecho: OUT a GPIO16
□ Verificar alineación de 3 sensores en línea recta
```

## Paso 5b: Sensores de obstáculos traseros

```
□ Ultrasónico HC-SR04: TRIG a GPIO5, ECHO a GPIO6 (CON DIVISOR 1k-2k)
□ IR trasero izquierdo: OUT a GPIO8
□ IR trasero derecho: OUT a GPIO9
□ Verificar conexión de tierra común
```

□ LED verde (sano): GPIO12 con R220Ω a GND (2 unidades)
□ LED amarillo (atención): GPIO24 con R220Ω a GND (2 unidades)
□ LED rojo (peligro): GPIO26 con R220Ω a GND (2 unidades)
□ LED azul (heartbeat): GPIO20 con R220Ω a GND (4 unidades)
□ Buzzer: GPIO21 a positivo, GND a negativo
```

## Paso 7: Cámaras

```
□ USB frontal: Puerto USB superior izquierdo
□ USB lateral izq: Puerto USB superior derecho
□ USB lateral der: Puerto USB inferior izquierdo
□ Etiquetar físicamente cada cámara
```

## Paso 8: Enfriamiento activo

```
□ Montar 2× ventiladores 12V en disipador/enclosure
  - Alimentación: Directamente desde BMS (12V)
  - Aislamiento: Usar aislante entre ventilador y Pi 5
□ Montar 1× ventilador 5V adicional
  - Alimentación: Desde step-down (5.1V)
  - Función: Enfriamiento complementario
□ Configurar control de velocidad (PWM opcional)
  - Baja velocidad: si T < 55°C
  - Media velocidad: si 55°C < T < 65°C
  - Alta velocidad: si T > 65°C
□ Verificar flujo de aire hacia disipador principal
□ Futuro: Agregar más ventiladores 5V según resultados térmicos
```

## Paso 9: Validación

```
□ Enciender solo energía (sin Pi 5)
□ Verificar 5.1V estables en step-down
□ Encender Pi 5
□ Probar cada LED (debe brillar)
□ Probar buzzer (debe emitir sonido)
□ Probar sensores uno por uno
□ Probar motores en baja velocidad
□ Verificar cámaras USB con software
```

---

# 9. CHECKLIST CRÍTICO ANTES DE ENCENDER

```
ENERGÍA:
□ Batería (BMS) conectada a step-down correctamente
□ Step-Down ajustado a 5.1V exacto (multímetro sin carga)
□ GND común unido: batería, L298N, Pi 5, sensores, LCD
□ Cables gruesos (12AWG mín) en batería → L298N
□ Cables medianos (18AWG) en motores

PROTECCIONES:
□ HC-SR04 ECHO CON DIVISOR 1k-2k (OBLIGATORIO)
□ LEDs con resistencias 220Ω
□ Motores protegidos por L298N (fusible 2A)
□ Sensores alimentados a 5V (no 12V)

CONEXIONES:
□ Motores izq y der giran en MISMA DIRECCIÓN
□ LCD I2C dirección verificada (0x27 o 0x3F)
□ Cámaras USB etiquetadas y probadas
□ Jumpers de color correctamente distribuidos

FÍSICA:
□ Sin cables sueltos o cortocircuitos visibles
□ Disipadores en step-down y L298N si es necesario
□ Fan de enfriamiento funcionando
□ BMS protegido del contacto accidental
```

---

# 10. MAPA RESUMIDO DE CONEXIONES

```text
GPIO LISTA RÁPIDA:

CONTROL:
  GPIO17 → L298N IN1
  GPIO27 → L298N IN2
  GPIO22 → L298N IN3
  GPIO23 → L298N IN4
  GPIO18 → L298N ENA (PWM)
  GPIO25 → L298N ENB (PWM)

SENSORES DE LÍNEA:
  GPIO13 → Line Follower LEFT (MH-B izq)
  GPIO19 → Line Follower CENTER (TCRT5000)
  GPIO16 → Line Follower RIGHT (MH-B der)

SENSORES DE OBSTÁCULOS:
  GPIO5  → HC-SR04 TRIG
  GPIO6  → HC-SR04 ECHO (con divisor 1k-2k)
  GPIO8  → IR trasero izquierda (proximidad)
  GPIO9  → IR trasero derecha (proximidad)

INTERFAZ:
  GPIO2  → LCD SDA
  GPIO3  → LCD SCL
  GPIO21 → Buzzer
  GPIO12 → LED verde (sano)
  GPIO24 → LED amarillo (atención)
  GPIO26 → LED rojo (peligro)
  GPIO20 → LED azul (heartbeat)

ALIMENTACIÓN:
  Pin 1  → +3.3V
  Pin 2, 4 → +5V
  Pin 6, 9, 14, 20, 25, 30, 34, 39 → GND

ENERGÍA EXTERNA:
  BMS 12.6V → Step-Down 5.1V (entrada)
            → Ventilador 12V (entrada) — operación activa
  Step-Down 5.1V → Pi 5, sensores, LCD
  Step-Up 12.6V → BMS (carga)
               → Ventilador 12V — durante carga
  Agrupador AA 4.8V → Regulador 5V → 3× Ventiladores 5V
                                     (Pi 5 + 2× L298N)
```

---

# 11. ERRORES COMUNES Y SOLUCIONES

## HC-SR04 sin divisor
**Síntoma:** Pi 5 se reinicia aleatoriamente o GPIO6 muere  
**Solución:** AGREGAR DIVISOR 1k-2k inmediatamente. **CRÍTICO.**

## Motores giram opuestos
**Síntoma:** Robot gira o tira a un lado  
**Solución 1 (hardware):** Intercambia dos cables del motor que gira mal  
**Solución 2 (software):** Invierte lógica GPIO para ese motor

## LCD no enciende
**Síntoma:** Pantalla en blanco o solo carácter  
**Causa probable 1:** GND/VCC invertidos  
**Causa probable 2:** Dirección I2C incorrecta (ejecutar `i2cdetect -y 1`)

## Step-Down con voltaje incorrecto
**Síntoma:** Pi 5 arranca lentamente o se reinicia  
**Solución:** Ajustar potenciómetro step-down a 5.1V exacto con multímetro

## BMS no carga o descarga
**Síntoma:** Pack muerto (0V)  
**Causa:** Celdas descargadas por debajo de 2.5V  
**Solución:** Cargar cada celda individualmente a 4.2V, luego reconectar

## Sensores IR no detectan
**Síntoma:** GPIO siempre lee 0 o 1  
**Causa probable 1:** Sensor reflectante sucio  
**Causa probable 2:** Polaridad VCC/GND invertida  
**Solución:** Limpiar lentes, verificar conexiones

---

# 12. NOTAS FINALES

## Compatibilidad de GPIO
La **Raspberry Pi 5** es compatible con Pi 4/3B+ en pinout (40 pines).  
Todos los pines GPIO trabajan a **3.3V**, no 5V.  
**Máximo 16mA por GPIO** — para carga mayor, usar transistor o relé.

## Sobre el L298N
- **Protección:** Fusible interno ~2A por salida
- **Disipación:** Se calienta con cargas sostenidas; agregar disipador si es necesario
- **Eficiencia:** ~85% (pierde ~15% en calor)

## Sobre el PWM en ENA/ENB
- **Rango:** 0-255 (digitalWritePWM)
- **Frecuencia:** 490Hz típico (Raspberry Pi)
- **Resolución:** 8 bits

## Sobre el Step-Down XL4015
- **Entrada máxima:** 12.6V (no exceder, daña regulador)
- **Corriente máxima:** 5A continuo
- **Eficiencia:** ~95%
- **Potenciómetro:** Ajustar con voltímetro en salida SIN CARGA

## Futuras mejoras
- Agregar TP4056 individual para cada par de celdas (mejor control)
- Implementar **telemetría de voltaje** (ADC GPIO para monitoreo)
- Agregar **relé de desconexión automática** si voltaje cae < 9.5V
- Integrar **carga inalámbrica** con bobinas en dock

---

**Versión:** 4.0  
**Última actualización:** 2025-05  
**Responsable:** Fer (Systems Engineering, Universidad Mariano Gálvez)  
**Estado:** Activo para Robot AgroTech Vivero con configuración 3S2P Li-ion y control PWM habilitado
