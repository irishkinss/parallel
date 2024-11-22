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

    def send_settings(self, settings):
        """Отправка настроек на сервер."""
        if self.connected:
            try:
                self.client_socket.sendall(str(settings).encode())
                print("Settings sent to server.")
            except Exception as e:
                print(f"Error sending settings: {e}")

    def close(self):
        """Закрытие соединения с сервером."""
        if self.client_socket:
            self.client_socket.close()
            print("Connection closed.")

class SimulationGUI(tk.Tk):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.title("Simulation GUI")

        # Настройка весов для строк и столбцов
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=2)  # График
        self.grid_columnconfigure(1, weight=1)  # Управление

        # Фрейм для 3D-графика
        self.canvas_frame = ttk.Frame(self)  
        self.canvas_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Фрейм для управления
        self.control_frame = ttk.Frame(self)  # Изменено: родительский виджет - self
        self.control_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        # Элементы управления (слайдеры, кнопки и т.д.)
        self.temperature_label = ttk.Label(self.control_frame, text="Температура")
        self.temperature_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.temperature_slider = ttk.Scale(self.control_frame, from_=0, to_=100, orient="horizontal")
        self.temperature_slider.grid(row=0, column=1, padx=5, pady=5)

        self.viscosity_label = ttk.Label(self.control_frame, text="Вязкость")
        self.viscosity_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)

        self.viscosity_slider = ttk.Scale(self.control_frame, from_=0, to_=100, orient="horizontal")
        self.viscosity_slider.grid(row=1, column=1, padx=5, pady=5)

        self.size_label = ttk.Label(self.control_frame, text="Размер")
        self.size_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)

        self.size_slider = ttk.Scale(self.control_frame, from_=0, to_=100, orient="horizontal")
        self.size_slider.grid(row=2, column=1, padx=5, pady=5)

        self.mass_label = ttk.Label(self.control_frame, text="Масса")
        self.mass_label.grid(row=3, column=0, sticky="w", padx=5, pady=5)

        self.mass_slider = ttk.Scale(self.control_frame, from_=0, to_=100, orient="horizontal")
        self.mass_slider.grid(row=3, column=1, padx=5, pady=5)

        self.frequency_label = ttk.Label(self.control_frame, text="Кол-во частиц")
        self.frequency_label.grid(row=4, column=0, sticky="w", padx=5, pady=5)

        self.frequency_slider = ttk.Scale(self.control_frame, from_=0, to_=100, orient="horizontal")
        self.frequency_slider.grid(row=4, column=1, padx=5, pady=5)

        self.apply_button = ttk.Button(self.control_frame, text="Применить", command=self.apply_settings)
        self.apply_button.grid(row=5, column=0, padx=5, pady=5)

        self.reset_button = ttk.Button(self.control_frame, text="Сбросить", command=self.reset_settings)
        self.reset_button.grid(row=5, column=1, padx=5, pady=5)

        # Лог и кнопки управления
        self.log_label = ttk.Label(self.control_frame, text="Лог")
        self.log_label.grid(row=6, column=0, sticky="w", padx=5, pady=5)

        self.log_text = tk.Text(self.control_frame, height=10, width=40)
        self.log_text.grid(row=7, column=0, columnspan=2, padx=5, pady=5)

        self.start_button = ttk.Button(self.control_frame, text="Запуск", command=self.start_simulation)
        self.start_button.grid(row=8, column=0, padx=5, pady=5)

        self.stop_button = ttk.Button(self.control_frame, text="Стоп", command=self.stop_simulation)
        self.stop_button.grid(row=8, column=1, padx=5, pady=5)

        # Создаем виджет для 3D-графика
        fig = plt.figure()
        self.ax = fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, padx=5, pady=5, sticky="nsew")    


    def apply_settings(self):
        # Применение настроек
        self.log_text.insert(tk.END, "Параметры применены\n")

    def reset_settings(self):
        # Сброс настроек
        self.log_text.insert(tk.END, "Параметры сброшены\n")

    def start_simulation(self):
        # Старт симуляции
        self.log_text.insert(tk.END, "Симуляция запущена\n")
        self.client.send_message("START")

    def stop_simulation(self):
        # Стоп симуляции
        self.log_text.insert(tk.END, "Симуляция остановлена\n")
        self.client.send_message("STOP")
        
    def on_closing(self):
        """Обработка закрытия окна."""
        self.client.close()
        self.destroy()

if __name__ == "__main__":
    client = Client()
    app = SimulationGUI(client)
    app.mainloop()
    client.close()
