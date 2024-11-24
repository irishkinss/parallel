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
            # Установка тайм-аута для сокета
            client_socket.settimeout(10)  # 10 секунд тайм-аута

            while True:
                # Получаем настройки от клиента
                settings_data = client_socket.recv(1024).decode()
                if not settings_data:
                    break  # Если данные пустые, закрываем соединение

                print(f"Получены настройки: {settings_data}")
                
                # Безопасное преобразование настроек
                try:
                    settings = json.loads(settings_data)
                except json.JSONDecodeError:
                    print("Ошибка декодирования JSON")
                    break

                # Безопасное получение параметров
                temperature = float(settings.get('temperature', 300))
                particle_count = int(settings.get('frequency', 100))
                
                # Создание частиц
                self.particles = [
                    Particle(
                        random.uniform(0, 1), 
                        random.uniform(0, 1), 
                        random.uniform(0, 1), 
                        0.01, 
                        1.0, 
                        temperature
                    ) for _ in range(particle_count)
                ]

                # Отправка координат частиц
                coordinates = [(p.x, p.y, p.z) for p in self.particles]
                try:
                    # Преобразуем в формат списка списков
                    client_socket.sendall(json.dumps(coordinates).encode())
                    print(f"Отправлены координаты {len(coordinates)} частиц")
                except Exception as send_error:
                    print(f"Ошибка отправки данных: {send_error}")
                    break

                # Небольшая пауза между итерациями
                time.sleep(0.5)

        except socket.timeout:
            print("Тайм-аут соединения")
        except Exception as e:
            print(f"Ошибка обработки клиента: {e}")
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