# Informe de arquitectura, funcionalidades, estructura y fallos

Fecha de corte: 2026-06-04
Workspace: `C:\Proyecto_IA_Vivero`
Superficie operativa principal revisada: `worktrees/release`
Documentacion revisada: inventario completo de `documentacion_local_raiz` y `documentacion_local_raiz/mods` con 56 archivos `.md`; lectura completa de los documentos vigentes principales de arquitectura, integracion, Nginx/VM, IA local, QR/camaras y voz; barrido global de titulos, pendientes, riesgos, fallos y mejoras.

## 1. Resumen ejecutivo

El proyecto ya tiene una base integrada considerable: backend Spring Boot, frontend React/Vite servido por Nginx en el stack release, PostgreSQL, runtime Python para Raspberry Pi, control de robot, stream de video, comandos por voz, observaciones, analisis de planta, reportes PDF y preparacion de VM con Qwen/vLLM.

La arquitectura real vigente ya no es la de los documentos antiguos que hablan de `robot-bridge` como centro. La direccion actual es:    

```text
Raspberry Pi 5
  -> captura, motores, sensores, QR, stream, heartbeat, observaciones
  -> backend Spring Boot
      -> estado, comandos, cola, persistencia, analisis, reportes, PDF, notificaciones
      -> PostgreSQL e imagenes persistidas
  -> frontend React
      -> operacion, control, analisis, reportes, voz y visualizacion
```

El punto mas importante: el codigo compila en frontend y backend. Lo que falta no es "empezar el sistema", sino cerrar integracion real, contratos, validacion fisica, seguridad de configuracion, pruebas automatizadas y despliegue final.

## 2. Verificaciones ejecutadas hoy

- `npm.cmd run build` en `worktrees/release/vivero-frontend`: OK.
- `mvn -q -DskipTests compile` en `worktrees/release/vivero-backend`: OK.
- Validacion AST Python sin escribir bytecode en `worktrees/release/robot-pi`: OK para 16 archivos principales.
- `docker compose -f worktrees/release/docker-compose.yml ps`: el stack no esta levantado actualmente; solo devolvio encabezado y warning de `version` obsoleto.
- Estado Git `worktrees/release`: cambios locales solo en `.env`, `robot-pi/.env` y backups locales no versionados.

## 3. Checklist de lo que ya tenemos

### Arquitectura y despliegue

- [x] Worktree operativo principal en `worktrees/release`.
- [x] Stack local con `db`, `backend` y `frontend`.
- [x] Frontend servido con Nginx, no con Vite dev server en produccion local.
- [x] Proxy Nginx para `/api` y `/api/ws`.
- [x] Compose VM separado en `docker-compose.vm.yml`.
- [x] Preparacion de servicio `vlm-qwen` para VM GPU.
- [x] Healthcheck de frontend y backend documentados.
- [ ] Stack no esta corriendo al momento de este informe.
- [ ] TLS/dominio de produccion pendiente.
- [ ] Qwen/vLLM reportado como corriendo en VM; falta actualizar backend para consumirlo y validar inferencia end-to-end.

### Backend

- [x] Spring Boot 3.2.4 con Java 17.
- [x] Seguridad JWT, roles y filtros.
- [x] Modulo auth.
- [x] Modulo robot: comandos, heartbeat, observaciones, cola y ACK.
- [x] WebSocket STOMP para estado.
- [x] WebSocket raw para stream de robot.
- [x] Modulo reports: generacion, PDF, notificaciones y configuracion de canales.
- [x] Modulo analisis: analisis de planta, historial, imagenes y fallback.
- [x] Persistencia JPA/PostgreSQL.
- [x] Manejo global de errores.
- [ ] Cliente real hacia `vlm-qwen:8000/v1` todavia no implementado.
- [x] Telemetria extendida de la Pi modelada en backend para `currentSpeedPercent`, `rearObstacleDetected` y `lastWatchdogReason`.
- [x] `mail.smtp.auth` configurable por `MAIL_SMTP_AUTH`.

### Frontend

- [x] React + Vite + TypeScript.
- [x] Rutas: login, dashboard, plantas, patrullajes, robot, goto, reportes, analisis, usuarios.
- [x] Proteccion de rutas y fallback por rol.
- [x] Control de robot por botones/teclado.
- [x] Consumo de estado robot por STOMP/SockJS.
- [x] Consumo de stream raw por WebSocket en `useRobotStream`.
- [x] Polyfill de `global` antes de imports de app para evitar crash de `sockjs-client`.
- [x] Voz con parser multi-comando, cola, reinicio de microfono y acciones reales del robot.
- [x] Reportes con apertura PDF autenticada por Axios/Blob.
- [x] Analisis con modo prueba, manual y profundo.
- [ ] Matriz RBAC final por vista/accion no esta cerrada.
- [ ] Voz no cubre todas las pantallas ni formularios.
- [ ] UX final responsive/control tactil necesita pulido.

### Runtime Raspberry Pi

- [x] Runtime Python separado.
- [x] Motores, sensores, LCD, LEDs, buzzer.
- [x] Heartbeat hacia backend.
- [x] Polling de comandos y ACK.
- [x] Stream de frames por WebSocket raw.
- [x] QR multi-candidato y orden espacial por camara documentado.
- [x] Resolucion QR diferida y cola offline.
- [x] Configuracion por `.env`.
- [ ] Validacion de campo con hardware real pendiente.
- [ ] Captura en movimiento requiere validacion fisica con hardware real.
- [x] ROI relativa a QR implementada para asociar planta correcta.
- [x] Telemetria extendida enviada por Pi ya cruza backend en codigo; falta prueba runtime.

### IA y dataset

- [x] Dataset y entrenamiento viven separados del runtime productivo.
- [x] Modelo TFLite historico rapido disponible.
- [x] Benchmarks documentados del modelo historico: rapido pero debil, especialmente `atencion`.
- [x] Plan de mejora de dataset documentado.
- [x] Modelo jerarquico v5 documentado y artefactos ubicados en `modelos/hibrido_v5_jerarquico`.
- [ ] V5 no esta integrado en backend.
- [ ] Qwen/vLLM ya esta corriendo en VM segun validacion operativa del usuario, pero todavia no participa en inferencia backend.
- [ ] Criterio final de aceptacion de modelo productivo debe reconfirmarse antes de reemplazar nada.

### Documentacion

- [x] `documentacion_local_raiz/mods` funciona como hub de continuidad.
- [x] Hay documentos recientes para Nginx, VM, IA, voz, QR, SMTP y estado operativo.
- [x] Hay pinout y documentacion electrica detallada.
- [ ] Hay documentos antiguos con arquitectura ya superada.
- [ ] Hay mojibake/encoding roto en varios `.md`.
- [ ] Falta un indice maestro vigente que marque que documentos son canonicos y cuales historicos.

## 4. Lo que falta implementar

1. Integracion real de IA local/VLM:
   - Cliente HTTP OpenAI-compatible hacia `vlm-qwen:8000/v1`.
   - Orquestacion: clasificador ligero -> seleccion de imagenes -> Qwen -> reporte consolidado.
   - Decision clara entre modelo historico, v5 jerarquico, Gemini y revision humana.

2. Contrato de telemetria Pi -> backend -> frontend:
   - Ya se agregaron en backend `currentSpeedPercent`, `rearObstacleDetected` y `lastWatchdogReason`.
   - Falta validar con Pi real y stack vivo que heartbeat, REST/WebSocket y frontend reflejen los datos.
   - Para produccion formal falta migracion SQL controlada; hoy depende de `ddl-auto=update`.

3. Captura no bloqueante en movimiento:
   - Ya existe rafaga asociada a camara/QR y avance con `QR_CAPTURE_SPEED`.
   - Falta validar que no rompa navegacion, enfoque ni seguridad con hardware real.

4. Asociacion robusta QR/planta:
   - ROI relativa al QR por camara/lado ya implementada.
   - Pruebas con dos y tres QR simultaneos.
   - Medicion de FOV aproximada si se necesita precision.

5. Despliegue produccion/VM:
   - Crear `.env.vm` real fuera del repo.
   - Configurar TLS.
   - Validar firewall: exponer solo 22/80/443.
   - Actualizar backend para consumir el Qwen que ya esta corriendo en VM y medir tiempos reales.
   - Probar backup/restore de DB e imagenes.

6. SMTP/reportes:
   - `mail.smtp.auth` ya es configurable.
   - Confirmar modo Gmail autenticado vs Google Workspace relay.
   - Probar llegada real a bandeja, spam, cuarentena, SPF/DKIM/DMARC.

7. RBAC y seguridad funcional:
   - Formalizar matriz de permisos por rol y accion.
   - Alinear roles documentados (`OPERATOR`) con roles reales del codigo (`CONTROLLER`).
   - Revisar permisos de configuracion de notificaciones, usuarios y analisis.

8. Pruebas:
   - Tests backend para reportes PDF, notificaciones, robot command queue, finalizacion de patrullaje y analisis.
   - Tests frontend de rutas/roles y smoke de paginas criticas.
   - Pruebas de contrato Pi-backend con payloads reales.
   - Prueba end-to-end con stack levantado.

## 5. Lo que hay que pulir

- Limpiar documentacion antigua o marcarla como historica.
- Corregir encoding/mojibake en documentos y comentarios.
- Mantener `docker-compose.yml` sin `version` obsoleto.
- Mantener `.env.example` y `robot-pi/.env.example` sin valores reales o redes privadas.
- Separar con mas claridad root de dataset vs `worktrees/release`.
- Reducir datos pesados/generados en el root o documentar politica de versionado.
- Pulir UX del frontend: botones menos redondeados, responsive de robot, estados vacios, errores de conexion y accesibilidad.
- Agregar observabilidad: logs de stream, tamano de frames, reconnects, latencia de IA, tiempo de reporte, estado de cola.
- Documentar comandos de arranque por superficie: root dataset, release, robot-pi, VM.

## 6. Reporte de lo que esta fallando o en riesgo

### Fallos confirmados hoy

1. El stack `release` no esta levantado.
   - Evidencia: `docker compose ps` no mostro servicios.
   - Impacto: no hay validacion viva de health, API, WebSocket, stream ni DB.

2. `docker-compose.yml` emitia warning por `version` obsoleto.
   - Estado 2026-06-09: cerrado; se elimino `version: "3.9"` y `docker compose config --quiet` queda limpio.
   - Impacto residual: ninguno conocido en compose release.

3. `py_compile` intento escribir en `__pycache__` y fallo por permisos.
   - Se valido despues con AST sin escribir bytecode.
   - Impacto: no indica error de sintaxis, pero el entorno tiene permisos restrictivos en esa carpeta.

### Fallos o brechas vigentes por codigo/documentacion

1. Telemetria extendida ya fue cerrada en codigo; falta validacion runtime.
   - La Pi envia `currentSpeedPercent`, `rearObstacleDetected`, `lastWatchdogReason`.
   - El frontend espera esos campos.
   - Backend ya los tiene en `RobotHeartbeatRequestDto`, `RobotStatus` y `RobotStatusResponseDto`.

2. Qwen/vLLM corriendo en VM, pero no integrado al backend.
   - Compose VM declara `vlm-qwen` y el servicio ya fue reportado como corriendo en la VM.
   - Backend tiene propiedades `vision.api.local-vlm`.
   - `PlantAnalysisServiceImpl` decide entre Gemini y fallback local; no llama Qwen.

3. SMTP relay por IP ya es configurable en backend, pero el envio real sigue fallando por configuracion externa.
   - `application.yml` ya permite `MAIL_SMTP_AUTH=false`.
   - Google Workspace rechazo el relay para la IP publica probada; falta allowlist/remitente/dominio.

4. Modelo IA historico no es confiable como diagnostico final.
   - Rapido, pero `atencion` es clase debil.
   - Sirve mejor como filtro/agregacion por rafaga que como verdad por imagen individual.

5. Modelo v5 jerarquico requiere cautela antes de produccion.
   - Documenta 100% recall en `atencion`, pero accuracy global 34%, recall `peligro` 0% y recall `sano` 2.08%.
   - Puede ser preventivo, pero no debe venderse como clasificador balanceado sin validacion humana/operativa.

6. Captura robot sigue con deuda de validacion fisica.
   - El objetivo es capturar evidencia en movimiento.
   - El codigo ya captura rafaga asociada al QR/camara, pero falta prueba real de navegacion, enfoque y asociacion planta-QR.

7. Asociacion planta-QR ya tiene ROI en codigo; falta calibracion real.
   - Multi-QR esta mejorado.
   - ROI adaptativo vertical/horizontal ya decide region de planta desde el QR detectado.

8. Documentacion con estados mixtos.
   - `PROJECT_STRUCTURE_*` y `SESSION_CONTINUITY_*` antiguos marcan como pendiente cosas que ya existen.
   - `mods` es mas vigente, pero no hay indice canonico final.

9. Secretos/configuracion local son sensibles.
   - `.env` y `robot-pi/.env` estan modificados localmente y no deben subirse.
   - `.env.example` del robot ya no contiene SSID/password reales; aun hay que cuidar claves Gemini/Wi-Fi en entornos locales.

## 7. Prioridad recomendada

### Prioridad 1: estabilizar contrato y runtime

- Levantar stack `release`.
- Confirmar health por `http://localhost:3000/health` y `http://localhost:3000/api/actuator/health`.
- Probar login, robot status, reportes, analisis y stream.
- Validar telemetria extendida con stack vivo y Pi real.

### Prioridad 2: cerrar fallos de operacion

- Configurar SMTP correctamente segun proveedor real.
- Probar envio real y llegada.
- Validar PDF regenerado y notificacion individual.
- Mantener `.env.example` sin secretos y revisar docs sensibles antes de publicar.

### Prioridad 3: robot fisico

- Probar stream con camaras reales.
- Validar QR multi-candidato.
- Validar y calibrar ROI por QR/planta.
- Medir bus I2C, LCD y MPU.

### Prioridad 4: IA

- No reemplazar modelo productivo hasta tener criterios medidos.
- Integrar VLM local contra el Qwen que ya esta corriendo en VM y medir respuesta real.
- Usar modelo local como filtro/preseleccion, no como diagnostico unico.

## 8. Cierre

El proyecto esta en fase avanzada de integracion, no en fase inicial. El mayor riesgo no es falta de codigo base, sino falsa sensacion de completitud: muchas piezas ya existen y compilan, pero varias aun no fueron validadas en ejecucion real con stack vivo, hardware, camaras, SMTP y VM GPU.

La siguiente sesion deberia empezar por levantar `worktrees/release`, validar endpoints vivos y probar el contrato de telemetria extendida con Pi real, porque esa ruta conecta directamente Pi, backend y frontend.

## 9. Revision de cumplimiento 2026-06-09

Esta revision actualiza el estado de los faltantes detectados el 2026-06-04. Se separa lo que ya quedo implementado en codigo de lo que aun necesita validacion fisica, infraestructura real o decision funcional.

### Checklist de faltantes

| Punto | Estado 2026-06-09 | Evidencia / nota |
|---|---:|---|
| ROI planta-QR | IMPLEMENTADO, pendiente prueba fisica | `worktrees/robot-pi/robot-pi/src/vision/plant_roi.py`, `main.py`, `camera_handler.py`, `config.py`, `.env.example` y `README.md` ya tienen ROI adaptativo por QR. |
| Medidas ROI vertical/horizontal | IMPLEMENTADO | Modo `PLANT_ROI_ORIENTATION=adaptive`. Vertical: `max(260, qr_w*4.0)` x `max(260, qr_h*6.0)`. Horizontal: `max(260, qr_w*5.0)` x `max(260, qr_h*4.0)`. Para QR 60x60: vertical 260x360; horizontal 300x260. |
| ROI se mueve con el QR | IMPLEMENTADO, pendiente robot real | El ROI se calcula desde la caja del QR detectado, usa la camara/posicion que encontro el QR y se limita dentro del frame. |
| ROI adaptativo a planta vertical/horizontal | IMPLEMENTADO | En `adaptive` compara perfil vertical y horizontal y elige el que encaja mejor en la imagen con menor ajuste contra bordes. |
| Captura asociada al QR detectado | IMPLEMENTADO, pendiente prueba fisica | `capture_observation_burst()` usa `qr_candidate`, incluye el frame de deteccion y captura rafaga desde la posicion/camara que encontro el QR. |
| Captura no bloqueante / en movimiento | PARCIAL | El flujo captura con avance a `QR_CAPTURE_SPEED` y rafaga por camara, pero falta prueba real para confirmar que no degrade navegacion, enfoque ni asociacion planta-QR. |
| Telemetria extendida Pi-backend-frontend | IMPLEMENTADO en codigo | Backend ya recibe/persiste/publica `currentSpeedPercent`, `rearObstacleDetected`, `lastWatchdogReason`; la Pi los envia y el frontend ya los consume. Falta validacion con stack vivo y Pi real. |
| SMTP `mail.smtp.auth` fijo | IMPLEMENTADO en configuracion | `MAIL_SMTP_AUTH`, STARTTLS, envelope-from, localhost y timeouts ya son configurables en `application.yml`, compose y docs. |
| Prueba SMTP real | FALLA EXTERNA/CONFIG WORKSPACE | Conectividad a `smtp-relay.gmail.com:587` OK, pero el relay rechazo con `550-5.7.1 Invalid credentials for relay [186.151.250.134]`. Falta allowlist/IP/remitente/dominio en Google Workspace. |
| Compose release con `version` obsoleto | CERRADO | Se elimino `version: "3.9"` de `worktrees/release/docker-compose.yml`; `docker compose config --quiet` queda limpio. |
| `.env.example` robot con Wi-Fi real | CERRADO | `WIFI_SSID` y `WIFI_PASSWORD` quedaron vacios en `worktrees/robot-pi/.env.example`. No se tocaron `.env` locales. |
| Cliente real a `vlm-qwen` | PENDIENTE | Qwen/vLLM ya esta corriendo en VM segun validacion del usuario y existen propiedades `vision.api.local-vlm`, pero `PlantAnalysisServiceImpl` sigue llamando Gemini/fallback; no hay cliente backend a Qwen/vLLM. |
| VM GPU / TLS / dominio | PARCIAL | Qwen ya esta reportado como vivo en VM; siguen pendientes TLS/dominio y prueba end-to-end desde backend. |
| RBAC por rol/pantalla | PENDIENTE | Seguridad base existe, pero falta matriz funcional validada por rol y pantalla. |
| Stack release vivo completo | PENDIENTE DE VALIDACION | No se certifico en esta revision login, health, reportes, analisis, WebSocket, robot status y stream con contenedores vivos. |
| E2E robot/camaras/hardware | PENDIENTE | Falta prueba con Pi, camaras reales, QR fisico, planta real, LCD, I2C/MPU y sensores. |
| Documentacion canonica / estados antiguos | PENDIENTE | Este informe queda actualizado, pero aun falta indice canonico que marque documentos viejos como historicos o reemplazados. |

### Validaciones ejecutadas en esta revision

- `git -C worktrees/robot-pi pull --ff-only`: rama robot ya estaba actualizada.
- `python -c ... ast.parse(...)`: ROI y runtime Python parsean correctamente sin escribir `__pycache__`.
- `mvn -q -DskipTests compile`: backend compila con telemetria extendida.
- `mvn -q -Dtest=RobotServiceTest test`: prueba de heartbeat cubre `currentSpeedPercent`, `rearObstacleDetected`, `lastWatchdogReason`.
- `docker compose -f worktrees/release/docker-compose.yml config --quiet`: compose release valida sin warning de `version`.
- `docker compose -f worktrees/release/docker-compose.vm.yml config --quiet`: compose VM valida.
- `mvn -q -Dtest=EmailNotificationServiceTest test`: servicio de correo pasa pruebas unitarias.
- `mvn -q -Dtest=ManualEmailRelaySmokeTest -Dmanual.mail.test=true test`: conecto al relay, pero Google rechazo por configuracion del relay/IP.

### Reporte de fallas vigentes despues de esta revision

1. SMTP no esta operativo de punta a punta.
   - El codigo ya permite configurar relay sin auth.
   - La falla actual es de Google Workspace/relay: IP `186.151.250.134` no autorizada o remitente/dominio no aceptado.

2. Qwen/vLLM sigue siendo infraestructura viva en VM, no funcionalidad integrada en backend.
   - Falta implementar cliente OpenAI-compatible hacia `VISION_LOCAL_VLM_URL`.
   - Falta criterio de seleccion `VISION_API_PROVIDER=local-vlm` o equivalente dentro de `PlantAnalysisServiceImpl`.

3. ROI esta listo en codigo, pero no certificado en planta real.
   - Falta correr prueba con QR real, camaras izquierda/derecha/frontal y planta real.
   - Hay que verificar si los offsets `1.6` lateral y `0.4` vertical centran bien la planta segun montaje fisico.

4. Telemetria extendida ya no es brecha de codigo, pero falta validacion runtime.
   - Debe probarse heartbeat Pi -> backend -> WebSocket/REST -> frontend.
   - Riesgo residual: columnas nuevas dependen de `spring.jpa.hibernate.ddl-auto=update`; para produccion formal conviene migracion SQL controlada.

5. Stack release completo sigue sin certificacion operativa actual.
   - Falta levantar contenedores y validar health, login, robot status, stream, analisis, reportes y PDF/email.

6. Documentacion sigue con deuda de canon.
   - `mods` queda como fuente mas vigente.
   - Falta indice final que marque documentos antiguos como historicos para evitar leer estados obsoletos como pendientes reales.
