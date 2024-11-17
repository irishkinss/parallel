import tkinter as tk
from tkinter import ttk
import json
from client import Client
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D

class SimulationGUI(tk.Tk):
    def __init__(self, server_host='127.0.0.1', server_port=12345):
        super().__init__()
        self.title("3D Brownian Motion Simulation")
        self.geometry("800x600")

        self.client = Client(server_host, server_port)
        self.client.connect()

        fig = Figure(figsize=(5, 5), dpi=100)
        self.ax = fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        params_frame = tk.Frame(self)
        params_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.params = {}
        self.params["Температура"] = self.create_parameter_field(params_frame, "Температура", "300")
        self.params["Вязкость"] = self.create_parameter_field(params_frame, "Вязкость", "0.001")
        self.params["Частицы"] = self.create_parameter_field(params_frame, "Частицы", "50")
        self.params["Масса"] = self.create_parameter_field(params_frame, "Масса", "1")
        self.params["Радиус"] = self.create_parameter_field(params_frame, "Радиус", "0.1")
        self.params["Объем куба"] = self.create_parameter_field(params_frame, "Объем куба", "10")
        self.params["Скорость анимации (dt)"] = self.create_parameter_field(params_frame, "Скорость анимации (dt)", "0.01")

        start_button = tk.Button(params_frame, text="Запуск", command=self.start_simulation)
        start_button.pack(fill=tk.X, pady=5)

        pause_button = tk.Button(params_frame, text="Пауза", command=self.pause_simulation)
        pause_button.pack(fill=tk.X, pady=5)

        stop_button = tk.Button(params_frame, text="Стоп", command=self.stop_simulation)
        stop_button.pack(fill=tk.X, pady=5)

    def create_parameter_field(self, frame, label, default_value):
        label = tk.Label(frame, text=label)
        label.pack()
        entry = tk.Entry(frame)
        entry.insert(0, default_value)
        entry.pack(fill=tk.X, padx=5, pady=5)
        return entry

    def start_simulation(self):
        if not self.client.connected:
            print("Нет подключения к серверу!")
            return

        params = {key: entry.get() for key, entry in self.params.items()}
        self.client.send_command(f"start:{json.dumps(params)}")
        self.update_particles()

    def update_particles(self):
        if not self.client.connected:
            return

        self.client.send_command("get_particles")
        data = self.client.client_socket.recv(4096)
        particle_states = json.loads(data.decode())

        self.ax.clear()
        for particle in particle_states:
            self.ax.scatter(particle["x"], particle["y"], particle["z"])
        self.canvas.draw()

        self.after(100, self.update_particles)

    def pause_simulation(self):
        if not self.client.connected:
            return
        self.client.send_command("pause")

    def stop_simulation(self):
        if not self.client.connected:
            return
        self.client.send_command("stop")

    def on_close(self):
        if self.client.connected:
            self.client.close()
        self.quit()

if __name__ == "__main__":
    app = SimulationGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()

