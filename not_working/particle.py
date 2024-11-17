import random

class Particle:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class Simulation:
    def __init__(self, particles, viscosity, temperature, dt):
        self.particles = particles
        self.viscosity = viscosity
        self.temperature = temperature
        self.dt = dt

    def process_particles(self, batch):
        for particle in batch:
            # Обновление позиции частицы на основе параметров
            particle.x += random.uniform(-1, 1) * self.dt
            particle.y += random.uniform(-1, 1) * self.dt
            particle.z += random.uniform(-1, 1) * self.dt

    def get_particle_states(self):
        return [{"x": p.x, "y": p.y, "z": p.z} for p in self.particles]

