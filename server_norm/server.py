import socket
import threading
import time
import random
from particle import Particle  # Импортируем ваш класс Particle

class Server:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.particles = [Particle(random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1), 0.01, 1.0) for _ in range(100)]
        self.server_socket = None

    def handle_client(self, client_socket):
        """Обработчик для клиентов."""
        try:
            while True:
                # Отправляем координаты частиц клиенту
                coordinates = [(particle.x, particle.y, particle.z) for particle in self.particles]
                client_socket.sendall(str(coordinates).encode())
                time.sleep(0.015)  # Обновляем каждые 15 мс
        except Exception as e:
            print(f"Error with client: {e}")
        finally:
            client_socket.close()

    def start(self):
        """Запуск сервера."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}")

        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                print(f"Accepted connection from {addr}")
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.start()

                # Обновление координат частиц
                while True:
                    for particle in self.particles:
                        particle.update_position(0.015, 0.1, 300)  # Примерные параметры для обновления
                    time.sleep(0.015)  # Обновляем каждую 15 мс
        except KeyboardInterrupt:
            print("\nServer is stopping...")
        finally:
            self.server_socket.close()
            print("Server socket closed.")

if __name__ == "__main__":
    server = Server()
    server.start()