import socket
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import ast
import json
from gui import SimulationGUI

class Client:
    def __init__(self, server_host='127.0.0.2', server_port=12345, gui = None):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = None
        self.connected = False
        self.gui = gui

    def connect(self):
        """Подключение к серверу."""
        try:
            self.client_socket = socket.create_connection((self.server_host, self.server_port), timeout=2)
            self.connected = True
            print("Connected to server.")
            return True
        except (socket.timeout, socket.error) as e:
            self.connected = False
            print(f"Failed to connect to server: {e}")
            return False

            
    def send_settings(self, settings):
        try:
            # Сначала проверяем подключение
            if not self.connected:
                # Если нет соединения, пытаемся подключиться
                if not self.connect():
                    print("Не удалось подключиться к серверу")
                    return False

            # Сохранение настроек в JSON файл
            with open('settings.json', 'w', encoding='utf-8') as file:
                json.dump(settings, file, ensure_ascii=False, indent=4)
                print("Настройки сохранены в settings.json")

            # Отправка настроек на сервер
            settings_data = json.dumps(settings)
            self.client_socket.sendall(settings_data.encode())
            print(f"Настройки отправлены на сервер: {settings}") 
            return True

        except Exception as e:
            print(f"Ошибка при сохранении настроек: {e}")
            return False
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

if __name__ == "__main__":
    client = Client()
    gui = SimulationGUI(client)
    gui.protocol("WM_DELETE_WINDOW", gui.on_closing)
    gui.mainloop()