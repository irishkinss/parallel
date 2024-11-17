import tkinter as tk
from tkinter import ttk
import socket
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import ast

class Client:
    def __init__(self, server_host='127.0.0.1', server_port=12345):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = None
        self.connected = False

    def connect(self):
        """Подключение к серверу."""
        try:
            self.client_socket = socket.create_connection((self.server_host, self.server_port), timeout=2)
            self.connected = True
            print("Connected to server.")
        except (socket.timeout, socket.error):
            self.connected = False
            print("Failed to connect to server.")

    def receive_coordinates(self, update_plot_callback):
        """Получение координат от сервера."""
        while self.connected:
            try:
                data = self.client_socket.recv(1024).decode()
                if data:
                    coordinates = ast.literal_eval(data)
                    # Вызов функции обновления графика в основном потоке
                    update_plot_callback(coordinates)
            except Exception as e:
                print(f"Error receiving data: {e}")
                self.connected = False

    def close(self):
        """Закрытие соединения с сервером."""
        if self.client_socket:
            self.client_socket.close()
            print("Connection closed.")

class SimulationGUI(tk.Tk):
    def __init__(self, client):
        super().__init__()
        self.title("Particle Simulation")
        self.geometry("800x600")
        
        self.client = client
        self.client.connect()

        # Создаем виджет для 3D-графика
        fig = plt.figure()
        self.ax = fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Запускаем поток для получения координат
        threading.Thread(target=self.client.receive_coordinates, args=(self.update_plot,), daemon=True).start()

    def update_plot(self, coordinates):
        """Обновление графика с новыми координатами."""
        # Используем метод after для обновления графика в основном потоке
        self.ax.clear()
        xs, ys, zs = zip(*coordinates)
        self.ax.scatter(xs, ys, zs)
        self.canvas.draw()

    def on_closing(self):
        """Обработка закрытия окна."""
        self.client.close()
        self.destroy()

if __name__ == "__main__":
    client = Client()
    gui = SimulationGUI(client)
    gui.protocol("WM_DELETE_WINDOW", gui.on_closing)
    gui.mainloop()