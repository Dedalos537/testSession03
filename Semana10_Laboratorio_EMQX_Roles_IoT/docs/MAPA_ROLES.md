# Mapa del laboratorio: capa → componente → rol

Este laboratorio **simula localmente** una arquitectura IoT. No despliega una nube pública real.

| Capa IoT | Componente del laboratorio | Rol profesional relacionado | Competencias observables |
|---|---|---|---|
| Percepción / Nodo | `sensor_simulator.py` | Embedded Device Engineer | adquisición de datos, estructura del payload, estado del dispositivo |
| Conectividad / Red | MQTT TCP 1883 | IoT Network & Connectivity Engineer | topics, QoS, conectividad, latencia, publicación/suscripción |
| Edge / Gateway | Docker + broker local | Edge Computing Developer | contenedores, servicios locales, disponibilidad |
| Plataforma | EMQX | IoT Platform / Cloud Engineer | broker, clientes, sesiones, monitoreo y gestión |
| Aplicación / Analítica | `monitor.py` + CSV | IoT Application / Data Engineer | consumo de mensajes, persistencia, preparación de datos |
| Seguridad transversal | análisis del laboratorio | IoT Security Engineer | autenticación, autorización, TLS, gestión de credenciales |

## Pregunta clave

¿Qué parte del sistema te gustaría administrar profesionalmente y qué competencias necesitarías demostrar?
