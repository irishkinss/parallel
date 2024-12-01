import socket
import threading
import time
import random
from particle import Particle
from mpi4py import MPI
import json  # Добавляем импортирование json модуля

class Server:
    def __init__(self, host='127.0.0.2', port=12345):
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.particles = []
        self.running = False
        self.simulation_thread = None

    def create_particles(self, settings):
        """Создание частиц с заданными параметрами"""
        print("[DEBUG] Создание частиц с параметрами:")
        print(f"Temperature: {settings['temperature']}")
        print(f"Viscosity: {settings['viscosity']}")
        print(f"Size: {settings['size']}")
        print(f"Mass: {settings['mass']}")
        print(f"Count: {settings['frequency']}")

        # Очищаем текущие частицы
        self.particles.clear()
        
        # Создаем новые частицы
        for _ in range(int(settings['frequency'])):
            particle = Particle(
                x=random.uniform(0, 1),
                y=random.uniform(0, 1),
                z=random.uniform(0, 1),
                radius=settings['size'],
                mass=settings['mass'],
                temperature=settings['temperature'],
                viscosity=settings['viscosity']
            )
            self.particles.append(particle)

    def simulate(self):
        """Основной цикл симуляции"""
        while self.running:
            try:
                # Обновляем позиции частиц
                for particle in self.particles:
                    particle.update_position(0.01)  # dt = 0.01 секунды

                # Собираем данные о частицах
                particles_data = []
                for particle in self.particles:
                    particles_data.append({
                        'x': particle.x,
                        'y': particle.y,
                        'z': particle.z
                    })

                # Преобразуем данные в JSON и получаем размер
                data = json.dumps(particles_data).encode()
                msg_size = len(data)

                # Отправляем размер сообщения (4 байта)
                self.client_socket.sendall(msg_size.to_bytes(4, byteorder='big'))
                
                # Отправляем само сообщение
                self.client_socket.sendall(data)
                    
                # Ждем подтверждения от клиента
                try:
                    self.client_socket.recv(1024)
                except:
                    print("Ошибка при получении подтверждения от клиента")
                    break

                time.sleep(0.01)  # Небольшая задержка для стабильной анимации

            except Exception as e:
                print(f"Ошибка в цикле симуляции: {e}")
                break

    def handle_client(self, client_socket):
        """Обработка подключения клиента"""
        try:
            # Получаем настройки
            data = client_socket.recv(1024).decode()
            settings = json.loads(data)
            print(f"Получены настройки: {data}")
            
            # Останавливаем текущую симуляцию если она запущена
            if self.running:
                self.running = False
                if self.simulation_thread:
                    self.simulation_thread.join()
            
            # Очищаем список частиц
            self.particles.clear()
            
            # Создаем частицы с новыми настройками
            self.create_particles(settings)
            
            # Запускаем симуляцию в отдельном потоке
            self.running = True
            self.simulation_thread = threading.Thread(target=self.simulate)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
            
        except Exception as e:
            print(f"Ошибка при обработке клиента: {e}")

    def start(self):
        """Запуск сервера"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            print(f"Server listening on {self.host}:{self.port}")

            while True:
                self.client_socket, addr = self.server_socket.accept()
                print(f"Accepted connection from {addr}")
                self.handle_client(self.client_socket)

        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.close()

    def close(self):
        """Закрытие сервера"""
        self.running = False
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=1.0)
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()

class MPIParticleSimulation:
    def __init__(self, settings):
        self.settings = settings
        self.server = Server()

    def setup_server(self):
        self.server.start()

    def simulate(self):
        # Непрерывная отправка координат
        while True:
            try:
                # Обновляем позиции частиц
                for particle in self.server.particles:
                    particle.update_position(0.05)

                # Проверяем столкновения между частицами
                for i in range(len(self.server.particles)):
                    for j in range(i + 1, len(self.server.particles)):
                        if self.server.particles[i].check_collision(self.server.particles[j]):
                            # Обмен скоростями при столкновении
                            self.server.particles[i].vx, self.server.particles[j].vx = self.server.particles[j].vx, self.server.particles[i].vx
                            self.server.particles[i].vy, self.server.particles[j].vy = self.server.particles[j].vy, self.server.particles[i].vy
                            self.server.particles[i].vz, self.server.particles[j].vz = self.server.particles[j].vz, self.server.particles[i].vz

                # Отправка координат
                coordinates = [(p.x, p.y, p.z) for p in self.server.particles]
                try:
                    # Отправляем длину сообщения первым
                    data = json.dumps(coordinates).encode()
                    length = len(data)
                    self.server.server_socket.send(length.to_bytes(4, byteorder='big'))
                    self.server.server_socket.sendall(data)
                    time.sleep(0.05)  # Задержка для стабильной анимации
                except (socket.error, BrokenPipeError) as e:
                    print(f"Ошибка отправки данных: {e}")
                    raise  # Пробрасываем ошибку выше для обработки
            
            except Exception as e:
                print(f"Ошибка в цикле симуляции: {e}")
                break

    def close(self):
        self.server.close()

def main():
    """Основная функция сервера"""
    try:
        # Загружаем настройки по умолчанию
        settings = {
            'temperature': 300,  # K
            'viscosity': 1e-3,  # Па·с
            'size': 1e-6,      # м
            'mass': 1e-18,     # кг
            'frequency': 10    # частиц
        }

        # Создаем экземпляр симуляции
        simulation = MPIParticleSimulation(settings)
        
        # Настраиваем сервер
        simulation.setup_server()
        
        # Запускаем симуляцию
        print("Запуск симуляции...")
        simulation.simulate()
        
        # Закрываем соединения
        simulation.close()
        
    except Exception as e:
        print(f"Ошибка в главной функции: {e}")
        
    finally:
        # Финализируем MPI
        MPI.Finalize()

if __name__ == "__main__":
    main()