import numpy as np
import math
import concurrent.futures
from threading import Barrier

# The `Particle` class represents a particle in a simulation with properties such as position
# (x, y, z), radius, mass, and temperature. When a `Particle` object is created, it initializes
# its position and velocity components randomly based on a given temperature. The
# `calculate_velocity` method calculates the initial velocity components based on the given
# temperature and random angles.
class Particle:
    def __init__(self, x, y, z, radius, mass, temperature):
        self.x = x
        self.y = y
        self.z = z
        self.radius = radius
        self.mass = mass
        self.temperature = temperature
        
        theta = np.random.uniform(0, math.pi)
        phi = np.random.uniform(0, 2 * math.pi)
        self.vx = 0
        self.vy = 0
        self.vz = 0
        self.calculate_velocity(theta, phi, temperature)

    def calculate_velocity(self, theta, phi, temperature):
        k = 1.380649e-23
        vrms = math.sqrt((3 * k * temperature) / self.mass)
        self.vx = vrms * math.sin(theta) * math.cos(phi)
        self.vy = vrms * math.sin(theta) * math.sin(phi)
        self.vz = vrms * math.cos(theta)

    def stochastic_deviation(self, viscosity, temperature, dt):
        k = 1.380649e-23
        D = k * temperature / (6 * math.pi * viscosity * self.radius)
        deviation = np.random.normal(0, math.sqrt(D * dt))
        return deviation

    def update_position(self, dt, viscosity, temperature):
        dx = self.vx * dt + self.stochastic_deviation(viscosity, temperature, dt)
        dy = self.vy * dt + self.stochastic_deviation(viscosity, temperature, dt)
        dz = self.vz * dt + self.stochastic_deviation(viscosity, temperature, dt)
        
        self.x += dx
        self.y += dy
        self.z += dz

class Simulation:
    def __init__(self, particles, viscosity, temperature, dt):
        self.particles = particles
        self.viscosity = viscosity
        self.temperature = temperature
        self.dt = dt
        self.barrier = Barrier(len(particles) // 10 + (len(particles) % 10 > 0))

    def process_particles(self, particles_subset):
        """Перерасчет координат частиц в отдельном потоке."""
        for particle in particles_subset:
            particle.update_position(self.dt, self.viscosity, self.temperature)
        
        # Ждем, пока все потоки завершат работу с координатами
        self.barrier.wait()

    def handle_collisions(self):
        """Обработка столкновений со стенками и между частицами."""
        for particle in self.particles:
            # Столкновение со стенками куба
            if particle.x <= 0 or particle.x >= 1:
                particle.vx = -particle.vx
            if particle.y <= 0 or particle.y >= 1:
                particle.vy = -particle.vy
            if particle.z <= 0 or particle.z >= 1:
                particle.vz = -particle.vz
            # Столкновения между частицами
            for other in self.particles:
                if other != particle and self.check_collision(particle, other):
                    self.resolve_collision(particle, other)

    def check_collision(self, particle1, particle2):
        """Проверка столкновения между двумя частицами."""
        distance = math.sqrt((particle1.x - particle2.x) ** 2 +
                             (particle1.y - particle2.y) ** 2 +
                             (particle1.z - particle2.z) ** 2)
        return distance <= (particle1.radius + particle2.radius)

    def resolve_collision(self, particle1, particle2):
        """Абсолютно упругое соударение двух частиц."""
        # Простейшая модель обмена скоростями при столкновении
        particle1.vx, particle2.vx = particle2.vx, particle1.vx
        particle1.vy, particle2.vy = particle2.vy, particle1.vy
        particle1.vz, particle2.vz = particle2.vz, particle1.vz

    def run(self):
        """Основной цикл симуляции."""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Разбиваем частицы на подгруппы по 10 и запускаем для каждой подгруппы поток
            particles_batches = [self.particles[i:i + 10] for i in range(0, len(self.particles), 10)]
            while True:  # Основной цикл симуляции
                futures = [executor.submit(self.process_particles, batch) for batch in particles_batches]
                
                # Ожидание завершения всех потоков
                concurrent.futures.wait(futures)
                
                # Обработка столкновений
                self.handle_collisions()
