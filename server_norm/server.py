import socket
import threading
import time
import random
from particle import Particle
import json

class Server:
    def __init__(self, host='127.0.0.2', port=12345):
        self.host = host
        self.port = port
        self.particles = []
        self.server_socket = None

    def handle_client(self, client_socket):
        """Обработчик для клиентов."""
        try:
            while True:
                # Получаем настройки от клиента
                settings_data = client_socket.recv(1024).decode()
                if settings_data:
                    settings = eval(settings_data)  # Преобразуем строку в словарь
                    temperature = settings.get('temperature', 300)  # Значение по умолчанию
                    particle_count = settings.get('frequency', 100)  # Количество частиц
                    self.particles = [Particle(random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1), 0.01, 1.0, temperature) for _ in range(particle_count)]

                # Создаем потоки для обработки частиц
                threads = []
                for i in range(0, len(self.particles), 5):  # Обрабатываем по 5 частиц за раз
                    thread = threading.Thread(target=self.process_particles, args=(client_socket, self.particles[i:i + 5]))
                    threads.append(thread)
                    thread.start()

                # Ждем завершения всех потоков
                for thread in threads:
                    thread.join()

                time.sleep(0.015)  # Обновляем каждые 15 мс
        except Exception as e:
            print(f"Error with client: {e}")
        finally:
            client_socket.close()

    def process_particles(self, client_socket, particles):
        """Обработка координат частиц и отправка их клиенту."""
        coordinates = [(particle.x, particle.y, particle.z) for particle in particles]
        # Отправляем координаты в формате JSON
        client_socket.sendall(json.dumps(coordinates).encode())

    def start(self):
        """Запуск сервера."""
        # Create socket with reuse address option
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"Server listening on {self.host}:{self.port}")

            while True:
                client_socket, addr = self.server_socket.accept()
                print(f"Accepted connection from {addr}")
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.start()
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.close()

if __name__ == "__main__":
    server = Server()
    server.start()