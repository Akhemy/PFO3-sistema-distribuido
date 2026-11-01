import socket
import threading
import queue
import json
import time

# Datos de conexion.
HOST = 'localhost'
PUERTO = 5000

# Cantidad de workers del pool. Son hilos fijos q se crean una sola vez
# al arrancar el servidor y se quedan esperando tareas.
CANT_WORKERS = 3

# Cola de tareas compartida. Los hilos q atienden clientes ponen las tareas acá
# y los workers las van sacando. queue.Queue ya es segura para usar entre hilos,
# asi q no hace falta un Lock. Cumple el papel de RabbitMQ pero dentro del programa.
cola_tareas = queue.Queue()


def procesar_tarea(tarea):
    """Ejecuta la tarea según su tipo y devuelve el resultado."""
    tipo = tarea.get('tipo')
    datos = tarea.get('datos', '')

    # Simulo q la tarea tarda un poco, asi se nota el reparto entre workers.
    time.sleep(2)

    if tipo == 'mayusculas':
        return datos.upper()
    elif tipo == 'invertir':
        return datos[::-1]
    elif tipo == 'sumar':
        # Los numeros llegan como texto separados por espacios. Si alguno no es
        # número, float() lanza ValueError y da un mensaje claro.
        try:
            numeros = [float(n) for n in datos.split()]
        except ValueError:
            raise ValueError('Solo se pueden sumar números.')
        return str(sum(numeros))
    else:
        raise ValueError('Tipo de tarea no válido.')


def worker(nombre):
    """Hilo del pool: saca tareas de la cola, las procesa y devuelve el resultado."""
    while True:
        # get() se queda esperando hasta q haya una tarea en la cola.
        tarea, cola_respuesta = cola_tareas.get()
        print(f'[{nombre}] procesando tarea: {tarea}')

        try:
            resultado = procesar_tarea(tarea)
            respuesta = {'estado': 'ok', 'resultado': resultado, 'worker': nombre}
        # Atrapo también AttributeError y TypeError por si llega una tarea mal armada
        # (por ejemplo, datos q no son texto). Asi el worker no se cae y el cliente
        # recibe un mensaje de error en vez de quedarse esperando.
        except (ValueError, AttributeError, TypeError) as e:
            respuesta = {'estado': 'error', 'mensaje': str(e), 'worker': nombre}

        # Devuelvo la respuesta al hilo q atiende a ese cliente.
        cola_respuesta.put(respuesta)


def iniciar_workers():
    """Crea el pool de workers."""
    for i in range(CANT_WORKERS):
        # daemon=True hace q los hilos se cierren solos cuando termina el programa.
        hilo = threading.Thread(target=worker, args=(f'worker-{i + 1}',), daemon=True)
        hilo.start()
    print(f'Pool de {CANT_WORKERS} workers iniciado.')


def atender_cliente(cliente, direccion):
    """Recibe las tareas de un cliente, las manda a la cola y le devuelve el resultado."""
    print(f'Conexión desde {direccion}')
    with cliente:
        # makefile() me deja leer el socket como si fuera un archivo de texto.
        # Leo línea por línea porq cada mensaje termina en '\n', asi sé dónde
        # termina cada tarea aunque TCP la entregue en partes.
        # El for termina solo cuando el cliente cierra la conexión.
        for linea in cliente.makefile('r', encoding='utf-8'):
            try:
                tarea = json.loads(linea)
            except json.JSONDecodeError:
                respuesta = {'estado': 'error', 'mensaje': 'Formato JSON inválido.'}
                cliente.sendall((json.dumps(respuesta) + '\n').encode('utf-8'))
                continue

            # Cada tarea lleva su propia cola de respuesta, asi el worker sabe
            # a quién devolverle el resultado.
            cola_respuesta = queue.Queue()
            cola_tareas.put((tarea, cola_respuesta))

            # Espero hasta q algún worker termine la tarea.
            respuesta = cola_respuesta.get()
            # Agrego '\n' al final para marcar dónde termina la respuesta.
            cliente.sendall((json.dumps(respuesta) + '\n').encode('utf-8'))

    print(f'Conexión cerrada con {direccion}')


def main():
    iniciar_workers()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
            servidor.bind((HOST, PUERTO))
            servidor.listen(5)
            print(f'Servidor escuchando en {HOST}:{PUERTO}')

            while True:
                cliente, direccion = servidor.accept()
                # Un hilo por cliente para recibir sus tareas.
                # Los workers del pool, sacan la tarea de la cola y la ejecutan.
                hilo = threading.Thread(target=atender_cliente, args=(cliente, direccion))
                hilo.start()

    except OSError as e:
        # Por ejemplo, si el puerto ya esta ocupado por otro programa.
        print(f'Error al iniciar el servidor: {e}')
    except KeyboardInterrupt:
        print('\nServidor detenido.')


if __name__ == '__main__':
    main()