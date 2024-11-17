import socket
import threading
import numpy as np
import tkinter as tk
from tkinter import ttk
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from gui import create_gui  # Импортируем функцию из другого файла

class SimulationClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.num_particles = 30
        self.cube_size = 5.0
        self.dt = 0.05
        self.positions = None
        self.simulation_running = False

        # Initialize GUI
        self.root = tk.Tk()
        self.root.title("3D Brownian Motion Simulation")

        # Create GUI elements
        self.param_frame, self.canvas_frame, self.fig, self.ax, self.canvas, self.start_button, self.stop_button = create_gui(self.root)

        self.client_socket_connected = False
        plt.show(block=False)

    def start_simulation(self):
        if not self.client_socket_connected:
            self.num_particles = int(self.param_frame['num_particles_entry'].get())
            self.cube_size = float(self.param_frame['cube_size_entry'].get())
            self.dt = float(self.param_frame['dt_entry'].get())

            # Connect to server
            try:
                self.client_socket.connect((self.host, self.port))
                self.client_socket_connected = True
                self.simulation_running = True

                # Start data receiving in a new thread
                threading.Thread(target=self.receive_data, daemon=True).start()
            except Exception as e:
                print(f"Error connecting to server: {e}")

    def stop_simulation(self):
        self.simulation_running = False
        self.client_socket.close()
        self.client_socket_connected = False

    def receive_data(self):
        while self.simulation_running:
            data = self.client_socket.recv(8 * self.num_particles * 3)
            if data:
                self.positions = np.frombuffer(data, dtype=np.float64).reshape(self.num_particles, 3)

    def update_plot(self, frame):
        if not self.simulation_running or self.positions is None:
            return
        self.ax.set_xlim(-self.cube_size/2, self.cube_size/2)
        self.ax.set_ylim(-self.cube_size/2, self.cube_size/2)
        self.ax.set_zlim(-self.cube_size/2, self.cube_size/2)
        self.scatter._offsets3d = (self.positions[:, 0], self.positions[:, 1], self.positions[:, 2])
        self.fig.canvas.draw_idle()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    client = SimulationClient(host="localhost", port=5555)
    client.run()

