# Robot Pi - Flujo Interno

## Flujo implementado hoy

1. El runtime carga configuracion, perifericos y modelo opcional al iniciar.
2. Un listener WebSocket escucha comandos en hilo separado.
3. Un emisor periodico manda heartbeat al backend.
4. En `FOLLOW_LINE`, el robot sigue linea y revisa obstaculos.
5. En el flujo actual, el QR detectado provoca transicion a `QR_DETECTED`.
6. El robot captura evidencia, clasifica localmente si aplica y envia observacion.
7. En `MANUAL`, responde a comandos y puede mantener stream activo.
8. El backend puede cambiar la camara activa del stream con `CAMERA_SELECT` o `SWITCH_CAMERA`.

## Flujo acordado para fase siguiente

1. Mantener avance en `AUTO_LINE`.
2. Detectar QR con laterales o camara dedicada.
3. Disparar rafaga de evidencia sin detener.
4. Etiquetar observacion con planta y mandar al backend.
5. Mantener la frontal para stream y obstaculos.

## Restriccion actual

Ese flujo objetivo no debe implementarse hasta autorizacion explicita del usuario.

## Comando de camaras

El runtime escucha `CAMERA_SELECT` y `SWITCH_CAMERA` para cambiar la camara activa del stream sin reiniciar el proceso.

Payloads validos:

```json
{ "camera": "front" }
{ "camera": "left" }
{ "camera": "right" }
{ "activeCamera": "front" }
```
