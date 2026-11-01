import socket
import json
import sys
import time

# Le indico a Python q use UTF-8 en la consola, asi los acentos se leen y
# se muestran bien en Windows (Como era en el PFO 1).
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

# Datos de conexion.
HOST = 'localhost'
PUERTO = 5000


def conectar_con_reintentos(intentos=3, espera=2):
    """Intenta conectarse al servidor varias veces antes de rendirse."""
    for intento in range(intentos):
        try:
            print(f'Intentando conectar (intento {intento + 1})...')
            cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente.connect((HOST, PUERTO))
            print(f'Conectado a {HOST}:{PUERTO}')
            return cliente
        except ConnectionRefusedError:
            # Pasa cuando el servidor no esta corriendo.
            print('No se pudo conectar: el servidor no responde.')
            cliente.close()
            time.sleep(espera)

    print('No se pudo establecer la conexión.')
    return None


def enviar_tarea(cliente, lector, tipo, datos):
    """Envía una tarea al servidor y devuelve la respuesta."""
    tarea = {'tipo': tipo, 'datos': datos}
    # Agrego '\n' al final para q el servidor sepa dónde termina la tarea.
    cliente.sendall((json.dumps(tarea) + '\n').encode('utf-8'))

    # Leo hasta el '\n' q marca el final de la respuesta. Si el servidor se
    # cayó, readline() devuelve vacío y json.loads lanza JSONDecodeError.
    respuesta = lector.readline()
    return json.loads(respuesta)


def mostrar_respuesta(respuesta):
    """Muestra el resultado o el error q devolvio el servidor."""
    if respuesta['estado'] == 'ok':
        print(f"Resultado: {respuesta['resultado']} (lo procesó {respuesta['worker']})")
    else:
        print(f"Error: {respuesta['mensaje']}")


def main():
    cliente = conectar_con_reintentos()
    if cliente is None:
        return

    # Relaciono cada opción del menú con el tipo de tarea del servidor.
    opciones = {'1': 'mayusculas', '2': 'invertir', '3': 'sumar'}

    with cliente:
        # Creo el lector una sola vez y lo uso para todas las respuestas.
        # Si creara uno nuevo en cada envío, cada uno tendría su propio buffer
        # y se podrían perder datos.
        lector = cliente.makefile('r', encoding='utf-8')

        while True:
            print('\n1. Pasar texto a mayúsculas')
            print('2. Invertir texto')
            print('3. Sumar números')
            print('4. Salir')
            opcion = input('Elegí una opción: ')

            if opcion == '4':
                break
            if opcion not in opciones:
                print('Opción no válida.')
                continue

            if opcion == '3':
                datos = input('Números separados por espacios: ')
            else:
                datos = input('Texto: ')

            try:
                print('Esperando resultado...')
                respuesta = enviar_tarea(cliente, lector, opciones[opcion], datos)
                mostrar_respuesta(respuesta)
            # ConnectionError incluye los errores de conexión reseteada, abortada
            # (el q suele aparecer en Windows) y tubería rota.
            except (ConnectionError, json.JSONDecodeError):
                # Si el servidor se cae a mitad de la sesión.
                print('Se perdió la conexión con el servidor.')
                break

    print('Cliente cerrado.')


if __name__ == '__main__':
    main()