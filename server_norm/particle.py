from mpi4py import MPI
import numpy as np
import random
import time
import socket
import json
import threading

class Particle:
    def __init__(self, x, y, z, radius=0.01, mass=1.0, temperature=300, viscosity=0.001):
        self.x = x
        self.y = y 
        self.z = z
        self.radius = radius
        self.mass = mass
        self.temperature = temperature
        self.viscosity = viscosity
        self.vx, self.vy, self.vz = self.calculate_velocity()

    def calculate_velocity(self):
        k = 1.380649e-23  # постоянная Больцмана
        vrms = np.sqrt((3 * k * self.temperature) / self.mass)
        theta = np.random.uniform(0, np.pi)
        phi = np.random.uniform(0, 2 * np.pi)
        
        vx = vrms * np.sin(theta) * np.cos(phi)
        vy = vrms * np.sin(theta) * np.sin(phi)
        vz = vrms * np.cos(theta)
        
        return vx, vy, vz

    def update_position(self, dt):
        # Стохастическое обновление с учетом вязкости
        D = (1.380649e-23 * self.temperature) / (6 * np.pi * self.viscosity * self.radius)
        
        noise_x = np.random.normal(0, np.sqrt(2 * D * dt))
        noise_y = np.random.normal(0, np.sqrt(2 * D * dt))
        noise_z = np.random.normal(0, np.sqrt(2 * D * dt))
        
        self.x += self.vx * dt + noise_x
        self.y += self.vy * dt + noise_y
        self.z += self.vz * dt + noise_z

        # Отскок от границ куба
        if self.x < 0 or self.x > 1:
            self.vx *= -1
        if self.y < 0 or self.y > 1:
            self.vy *= -1
        if self.z < 0 or self.z > 1:
            self.vz *= -1

    def check_collision(self, other):
        distance = np.sqrt(
            (self.x - other.x)**2 + 
            (self.y - other.y)**2 + 
            (self.z - other.z)**2
        )
        return distance <= (self.radius + other.radius)

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
        particles_per_process = self.num_particles // self.size
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

    def simulate(self):
        # Создаем частицы
        local_particles = self.create_particles()

        while True:
            # Обновляем позиции частиц
            for particle in local_particles:
                particle.update_position(0.005)  # dt = 5 мс

            # Проверяем столкновения внутри локальной группы частиц
            for i in range(len(local_particles)):
                for j in range(i+1, len(local_particles)):
                    if local_particles[i].check_collision(local_particles[j]):
                        # Упрощенная модель соударения
                        local_particles[i].vx, local_particles[j].vx = particles[j].vx, particles[i].vx
                        local_particles[i].vy, local_particles[j].vy = particles[j].vy, particles[i].vy
                        local_particles[i].vz, local_particles[j].vz = particles[j].vz, particles[i].vz

            # Синхронизируем состояния частиц
            all_particles_data = self.comm.allgather([
                (p.x, p.y, p.z) for p in local_particles
            ])

            # Отправляем координаты клиенту (только главный процесс)
            if self.rank == 0 and self.client_connection:
                coordinates = [
                    [p[0] for sublist in all_particles_data for p in sublist],
                    [p[1] for sublist in all_particles_data for p in sublist],
                    [p[2] for sublist in all_particles_data for p in sublist]
                ]
                
                try:
                    # Отправляем координаты в формате JSON
                    self.client_connection.send(json.dumps(coordinates).encode())
                except Exception as e:
                    print(f"Ошибка отправки данных: {e}")
                    break

            # Небольшая пауза
            time.sleep(0.005)

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