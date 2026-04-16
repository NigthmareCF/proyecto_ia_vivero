# Robot PI

1. El runtime carga configuracion, perifericos y modelo TFLite al iniciar.
2. Un listener WebSocket recibe comandos del backend en hilo separado.
3. El loop principal sigue linea, detecta QR con la camara frontal, captura imagenes izquierda/frontal/derecha y clasifica localmente.
4. Los resultados y el estado del robot se envian al bridge por HTTP.
5. En modo manual se activa el stream y los motores responden en tiempo real.
