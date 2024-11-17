import socket
import threading
import numpy as np
import time
import random

class SimulationServer:
    def __init__(self, host, port, num_particles, cube_size, dt):
        self.host = host
        self.port = port
        self.num_particles = num_particles
        self.cube_size = cube_size
        self.dt = dt
        self.positions = np.random.uniform(-cube_size / 2, cube_size / 2, (num_particles, 3))
        self.velocities = np.random.uniform(-1, 1, (num_particles, 3))
        self.lock = threading.Lock()
        self.clients = []
        self.stop_simulation = threading.Event()
        
    def handle_client(self, client_socket):
        while not self.stop_simulation.is_set():
            with self.lock:
                data = self.positions.tobytes()
            client_socket.sendall(data)
            time.sleep(self.dt)

    def update_particle_positions(self, start, end):
        while not self.stop_simulation.is_set():
            with self.lock:
                for i in range(start, end):
                    self.positions[i] += self.velocities[i] * self.dt
                    for j in range(3):
                        if abs(self.positions[i, j]) > self.cube_size / 2:
                            self.velocities[i, j] *= -1
            time.sleep(self.dt)

    def start_simulation(self):
        self.stop_simulation.clear()
        threads = []
        particles_per_thread = self.num_particles // 10
        for i in range(10):
            start = i * particles_per_thread
            end = start + particles_per_thread
            t = threading.Thread(target=self.update_particle_positions, args=(start, end))
            threads.append(t)
            t.start()
        
        for client_socket in self.clients:
            t = threading.Thread(target=self.handle_client, args=(client_socket,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()

    def stop(self):
        self.stop_simulation.set()
        for client_socket in self.clients:
            client_socket.close()

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen()
            print(f"Server listening on {self.host}:{self.port}")
            while True:
                client_socket, _ = server_socket.accept()
                self.clients.append(client_socket)
                print("Client connected")

if __name__ == "__main__":
    server = SimulationServer(host="localhost", port=5555, num_particles=100, cube_size=5.0, dt=0.05)
    threading.Thread(target=server.run).start()

