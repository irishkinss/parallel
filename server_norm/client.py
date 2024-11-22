import socket
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import ast
import json

class Client:
    def __init__(self, server_host='127.0.0.2', server_port=12345):
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
            
    def send_settings(self, settings):
        """Метод для отправки настроек серверу и записи их в файл в формате JSON."""
        try:
            # Отправляем настройки серверу
            settings_data = json.dumps(settings)  # Преобразуем словарь в JSON
            self.client_socket.sendall(settings_data.encode())
            print(f"Settings sent to server: {settings}")

            # Записываем настройки в файл
            with open("settings.json", "w") as file:
                json.dump(settings, file, indent=4)  # Форматируем JSON с отступами
            print("Settings saved to settings.json")
        except Exception as e:
            print(f"Error sending settings or saving to file: {e}")
    def receive_data(self):
        """Получение данных от сервера."""
        try:
            data = self.socket.recv(1024)
            return data.decode()
        except Exception as e:
            print(f"Error receiving data: {e}")
            
    def receive_coordinates(self):
        """Получение координат от сервера."""
        while self.connected:
            try:
                data = self.client_socket.recv(1024).decode()
                if data:
                    coordinates = ast.literal_eval(data)
                    self.update_plot(coordinates)
            except Exception as e:
                print(f"Error receiving data: {e}")
                self.connected = False

    def update_plot(self, coordinates):
        """Обновление графика с новыми координатами."""
        self.ax.clear()
        xs, ys, zs = zip(*coordinates)
        self.ax.scatter(xs, ys, zs)
        self.canvas.draw()

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
        threading.Thread(target=self.client.receive_coordinates, daemon=True).start()

    def on_closing(self):
        """Обработка закрытия окна."""
        self.client.close()
        self.destroy()

if __name__ == "__main__":
    client = Client()
    gui = SimulationGUI(client)
    gui.protocol("WM_DELETE_WINDOW", gui.on_closing)
    gui.mainloop()