import socket
import signal
import sys

def handle_client(client_socket, addr):
    """Обработчик для клиентов."""
    try:
        while True:
            message = client_socket.recv(1024).decode()
            if not message:
                break

            if message == "start":
                print("Starting simulation...")
            elif message == "pause":
                print("Pausing simulation...")
            elif message == "stop":
                print("Stopping simulation...")
            else:
                print(f"Received unknown command: {message}")
    finally:
        print(f"Client {addr} disconnected.")  # Сообщение о том, что клиент отключился
        client_socket.close()

def start_server(host='127.0.0.1', port=12345):
    """Запуск сервера."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Server listening on {host}:{port}")

    try:
        while True:
            client_socket, addr = server.accept()
            print(f"Accepted connection from {addr}")
            handle_client(client_socket, addr)
    except KeyboardInterrupt:
        print("\nServer is stopping...")
    finally:
        server.close()
        print("Server socket closed.")

if __name__ == "__main__":
    start_server()

