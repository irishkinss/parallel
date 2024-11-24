from mpi4py import MPI
import numpy as np
import random
import time
import socket
import json
import threading

class Particle:
    def __init__(self, x, y, z, radius, mass, temperature, viscosity):
        # Позиция
        self.x = x
        self.y = y
        self.z = z
        
        # Физические параметры
        self.radius = radius  # м
        self.mass = mass      # кг
        self.temperature = temperature  # K
        self.viscosity = viscosity      # Па·с
        
        # Константы
        self.k_b = 1.380649e-23  # Постоянная Больцмана, Дж/К
        
        # Рассчитываем параметры движения
        self.calculate_initial_velocities()
        
    def calculate_initial_velocities(self):
        """Рассчитываем начальные скорости на основе распределения Максвелла-Больцмана"""
        # Среднеквадратичная скорость: v_rms = sqrt(3kT/m)
        v_rms = np.sqrt(3 * self.k_b * self.temperature / self.mass)
        
        # Генерируем случайные компоненты скорости
        self.vx = np.random.normal(0, v_rms/np.sqrt(3))
        self.vy = np.random.normal(0, v_rms/np.sqrt(3))
        self.vz = np.random.normal(0, v_rms/np.sqrt(3))
        
    def update_position(self, dt):
        """Обновляем позицию частицы"""
        # Обновляем позиции с учетом скорости
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        
        # Добавляем случайное смещение (броуновское движение)
        D = self.k_b * self.temperature / (6 * np.pi * self.viscosity * self.radius)
        displacement = np.sqrt(2 * D * dt)
        
        self.x += np.random.normal(0, displacement)
        self.y += np.random.normal(0, displacement)
        self.z += np.random.normal(0, displacement)
        
        # Проверяем столкновения со стенками (упругие отражения)
        if self.x < 0:
            self.x = -self.x
            self.vx = -self.vx
        elif self.x > 1:
            self.x = 2 - self.x
            self.vx = -self.vx
            
        if self.y < 0:
            self.y = -self.y
            self.vy = -self.vy
        elif self.y > 1:
            self.y = 2 - self.y
            self.vy = -self.vy
            
        if self.z < 0:
            self.z = -self.z
            self.vz = -self.vz
        elif self.z > 1:
            self.z = 2 - self.z
            self.vz = -self.vz
            
        # Добавляем случайные изменения скорости
        # Это имитирует столкновения с молекулами среды
        velocity_perturbation = np.sqrt(self.k_b * self.temperature / self.mass) * 0.1
        
        self.vx += np.random.normal(0, velocity_perturbation)
        self.vy += np.random.normal(0, velocity_perturbation)
        self.vz += np.random.normal(0, velocity_perturbation)
    
    def check_collision(self, other):
        """Проверяем столкновение с другой частицей"""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        distance = np.sqrt(dx*dx + dy*dy + dz*dz)
        return distance < (self.radius + other.radius)

class MPIParticleSimulation:
    def __init__(self, settings):
        # Инициализация MPI
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()

        # Параметры из настроек
        self.settings = settings
        self.temperature = settings.get('temperature', 300)
        self.viscosity = settings.get('viscosity', 0.001)
        self.particle_radius = settings.get('size', 0.01)
        self.particle_mass = settings.get('mass', 1.0)
        self.num_particles = settings.get('frequency', 100)

        # Сокет для связи с клиентом
        self.server_socket = None
        self.client_connection = None
        
    def create_particles(self):
        # Создаем частицы для текущего процесса
        particles_per_process = max(1, self.num_particles // self.size)
        return [
            Particle(
                random.uniform(0, 1), 
                random.uniform(0, 1), 
                random.uniform(0, 1),
                radius=self.particle_radius,
                mass=self.particle_mass,
                temperature=self.temperature,
                viscosity=self.viscosity
            ) for _ in range(particles_per_process)
        ]

    def setup_server(self, host='127.0.0.2', port=12345):
        """Настройка сервера для обмена данными"""
        if self.rank == 0:  # Только главный процесс настраивает сервер
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((host, port))
            self.server_socket.listen(1)
            print(f"Сервер ожидает подключения на {host}:{port}")
            
            # Ожидание подключения клиента
            self.client_connection, addr = self.server_socket.accept()
            print(f"Подключен клиент: {addr}")

    def simulate(self, max_iterations=1000):
        # Создаем частицы
        local_particles = self.create_particles()
        iteration = 0
        dt = 0.01  # Шаг времени

        while iteration < max_iterations:
            # Обновляем позиции частиц
            for particle in local_particles:
                particle.update_position(dt)

            # Собираем данные со всех процессов
            if self.rank == 0 and self.client_connection:
                try:
                    # Собираем позиции частиц
                    positions = []
                    for particle in local_particles:
                        positions.append({
                            'x': particle.x,
                            'y': particle.y,
                            'z': particle.z,
                            'vx': particle.vx,
                            'vy': particle.vy,
                            'vz': particle.vz
                        })
                    
                    # Отправляем данные клиенту
                    data = json.dumps(positions)
                    self.client_connection.send(data.encode())
                    
                    # Получаем подтверждение от клиента
                    try:
                        self.client_connection.recv(1024)
                    except:
                        print("Ошибка при получении подтверждения от клиента")
                        break
                    
                except Exception as e:
                    print(f"Ошибка при отправке данных: {e}")
                    break

            iteration += 1
            time.sleep(0.01)  # Небольшая задержка для визуализации

    def close(self):
        """Закрытие соединений"""
        if self.client_connection:
            self.client_connection.close()
        if self.server_socket:
            self.server_socket.close()

def load_settings():
    """Загрузка настроек из файла"""
    try:
        with open('settings.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Настройки по умолчанию
        return {
            'temperature': 300,
            'viscosity': 0.001,
            'size': 0.01,
            'mass': 1.0,
            'frequency': 100
        }

def main():
    # Загружаем настройки
    settings = load_settings()

    # Создаем симуляцию
    simulation = MPIParticleSimulation(settings)

    try:
        # simulation.setup_server()
        simulation.simulate()
    finally:
        simulation.close()

if __name__ == "__main__":
    main()