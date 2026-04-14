# Robot PI

1. El runtime captura imagenes desde camara real o simulada.
2. El clasificador TFLite evalua la planta localmente.
3. El lector QR identifica la planta observada.
4. El controlador envia heartbeat y observacion al robot-bridge.
5. Si no hay hardware o librerias nativas, el sistema cae en modo simulacion.
