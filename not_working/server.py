import socket
import json
from concurrent.futures import ThreadPoolExecutor
from particle import Simulation, Particle

particles = []
simulation = None

def handle_start_command(params):
    global particles, simulation
    num_particles = int(params["Частицы"])
    particles = [Particle(...) for _ in range(num_particles)]
    simulation = Simulation(particles, float(params["Вязкость"]), float(params["Температура"]), float(params["Скорость анимации (dt)"]))

def send_particle_states(client_socket):
    if simulation:
        particle_states = simulation.get_particle_states()
        client_socket.sendall(json.dumps(particle_states).encode())

def handle_client(client_socket):
    try:
        while True:
            message = client_socket.recv(1024).decode()
            if message.startswith("start:"):
                params = json.loads(message[6:])
                handle_start_command(params)
            elif message == "get_particles":
                send_particle_states(client_socket)
            elif message == "pause":
                print("Pausing simulation...")
            elif message == "stop":
                print("Stopping simulation...")
    finally:
        client_socket.close()

def start_server(host='127.0.0.1', port=12345):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Server listening on {host}:{port}")

    with ThreadPoolExecutor() as executor:
        while True:
            client_socket, addr = server.accept()
            executor.submit(handle_client, client_socket)

if __name__ == "__main__":
    start_server()

