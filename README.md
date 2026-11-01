# PFO 3: Rediseño como Sistema Distribuido (Cliente-Servidor)

**Materia:** Programación sobre Redes
**Alumna:** Pamela Beatriz Olave Troncos

## Objetivo

Transformar el sistema en una arquitectura distribuida usando sockets: un servidor recibe tareas por socket y las reparte entre un pool de workers, y un cliente envía tareas y recibe los resultados.

## 1. Diagrama del sistema

![Diagrama del sistema distribuido](PFO%203%20%C2%B7%20Sistema%20distribuido%20cliente-servidor.drawio.png)

[Ver diagrama en Google Drive](https://drive.google.com/file/d/1hnRuhCldNJ8qZ92X4SnmccM7l9dNuJjx/view?usp=sharing)

| Componente | Función |
|---|---|
| **Clientes** (móvil, web, consola) | Envían las tareas al sistema. |
| **Balanceador de carga** (Nginx / HAProxy) | Reparte las conexiones entre los servidores para que ninguno se sature. |
| **Servidores workers** | Procesan las tareas con un pool de hilos, varias a la vez. |
| **Cola de mensajes** (RabbitMQ) | Comunica los servidores. Si uno está ocupado, la tarea espera en la cola. |
| **PostgreSQL y S3** | Guardan los datos de las tareas y los archivos. |

## 2. Implementación en Python

Versión simplificada del diagrama que corre en una sola máquina:

- `cliente.py`: se conecta por socket TCP a `localhost:5000` y envía tareas en JSON (pasar a mayúsculas, invertir texto o sumar números).
- `servidor.py`: crea un hilo por cliente, pone cada tarea en una `queue.Queue` (cumple el papel de RabbitMQ) y un pool de 3 hilos worker la procesa y devuelve el resultado.

Cada tarea tarda 2 segundos (`time.sleep`) para que se note cómo los workers se reparten el trabajo.

## Cómo ejecutarlo

Requisito: Python 3.8 o superior, sin librerías externas.

1. En una terminal: `python servidor.py`
2. En otra terminal: `python cliente.py`
3. Para ver el reparto entre workers, abrir 2 o 3 clientes a la vez.

## Estructura del repositorio

```
├── servidor.py
├── cliente.py
├── PFO 3 · Sistema distribuido cliente-servidor.drawio.png
└── README.md
```