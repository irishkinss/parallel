import tkinter as tk
from threading import Thread, Event
import numpy as np
import time

# Параметры симуляции
num_particles = 100
particles_per_thread = 10
temperature = 300
mass = 4.65e-26
D = 0.1
dt = 0.01
steps = 10
box_size = 10.0
radius = 0.1
k = 1.38e-23  # Константа Больцмана
Vrms = np.sqrt(3 * k * temperature / mass)

# Флаги для управления симуляцией
simulation_running = False
stop_event = Event()

# Основные функции симуляции
def stochastic_deviation(D, dt):
    return np.random.normal(0, np.sqrt(D * dt))

def calculate_velocity_projections(Vrms):
    theta = np.random.uniform(0, np.pi)
    phi = np.random.uniform(0, 2 * np.pi)
    Vx = Vrms * np.sin(theta) * np.cos(phi)
    Vy = Vrms * np.sin(theta) * np.sin(phi)
    Vz = Vrms * np.cos(theta)
    return Vx, Vy, Vz

def simulate_brownian_motion():
    global simulation_running
    particles = [{"position": np.random.uniform(0, box_size, 3)} for _ in range(num_particles)]
    while not stop_event.is_set():
        particle_groups = [particles[i:i + particles_per_thread] for i in range(0, num_particles, particles_per_thread)]
        all_positions = []
        all_velocities = []
        for group in particle_groups:
            positions, velocities = [], []
            for particle in group:
                x, y, z = particle["position"]
                Vx, Vy, Vz = calculate_velocity_projections(Vrms)
                for _ in range(steps):
                    x += Vx * dt + stochastic_deviation(D, dt)
                    y += Vy * dt + stochastic_deviation(D, dt)
                    z += Vz * dt + stochastic_deviation(D, dt)
                    if x < 0 or x > box_size: Vx = -Vx
                    if y < 0 or y > box_size: Vy = -Vy
                    if z < 0 or z > box_size: Vz = -Vz
                    x, y, z = min(max(x, 0), box_size), min(max(y, 0), box_size), min(max(z, 0), box_size)
                positions.append((x, y, z))
                velocities.append((Vx, Vy, Vz))
            all_positions.extend(positions)
            all_velocities.extend(velocities)
        print_simulation_results(all_positions, all_velocities)
        time.sleep(1)

def print_simulation_results(all_positions, all_velocities):
    for i, (pos, vel) in enumerate(zip(all_positions, all_velocities)):
        print(f"ID: {i + 1:3d} | Position: ({pos[0]:.5f}, {pos[1]:.5f}, {pos[2]:.5f}) | "
              f"Velocity: ({vel[0]:.5f}, {vel[1]:.5f}, {vel[2]:.5f})")

# Управляющие функции
def start_simulation():
    global simulation_running
    if not simulation_running:
        simulation_running = True
        stop_event.clear()
        Thread(target=simulate_brownian_motion, daemon=True).start()

def stop_simulation():
    global simulation_running
    simulation_running = False
    stop_event.set()

# Интерфейс с использованием tkinter
root = tk.Tk()
root.title("Brownian Motion Simulation")

start_button = tk.Button(root, text="Start Simulation", command=start_simulation)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="Stop Simulation", command=stop_simulation)
stop_button.pack(pady=10)

root.mainloop()

