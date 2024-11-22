import tkinter as tk
from tkinter import ttk
import socket
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import ast
from client import Client

# class Client:
#     def __init__(self, server_host='127.0.0.1', server_port=12345):
#         self.server_host = server_host
#         self.server_port = server_port
#         self.client_socket = None
#         self.connected = False

#     def connect(self):
#         """Подключение к серверу."""
#         try:
#             self.client_socket = socket.create_connection((self.server_host, self.server_port), timeout=2)
#             self.connected = True
#             print("Connected to server.")
#         except (socket.timeout, socket.error):
#             self.connected = False
#             print("Failed to connect to server.")

#     def receive_coordinates(self):
#         """Получение координат от сервера."""
#         while self.connected:
#             try:
#                 data = self.client_socket.recv(1024).decode()
#                 if data:
#                     coordinates = ast.literal_eval(data)
#                     self.update_plot(coordinates)
#             except Exception as e:
#                 print(f"Error receiving data: {e}")
#                 self.connected = False

#     def send_settings(self, settings):
#         """Отправка настроек на сервер."""
#         if self.connected:
#             try:
#                 self.client_socket.sendall(str(settings).encode())
#                 print("Settings sent to server.")
#             except Exception as e:
#                 print(f"Error sending settings: {e}")

#     def close(self):
#         """Закрытие соединения с сервером."""
#         if self.client_socket:
#             self.client_socket.close()
#             print("Connection closed.")

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
        self.temperature_value = ttk.Label(self.control_frame, text="0")  # Значение ползунка
        self.temperature_value.grid(row=0, column=2, padx=5, pady=5)

        self.viscosity_label = ttk.Label(self.control_frame, text="Вязкость")
        self.viscosity_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)

        self.viscosity_slider = ttk.Scale(self.control_frame, from_=0, to_=100, orient="horizontal")
        self.viscosity_slider.grid(row=1, column=1, padx=5, pady=5)
        self.viscosity_value = ttk.Label(self.control_frame, text="0")  # Значение ползунка
        self.viscosity_value.grid(row=1, column=2, padx=5, pady=5)

        self.size_label = ttk.Label(self.control_frame, text="Размер")
        self.size_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)

        self.size_slider = ttk.Scale(self.control_frame, from_=0, to_=100, orient="horizontal")
        self.size_slider.grid(row=2, column=1, padx=5, pady=5)
        self.size_value = ttk.Label(self.control_frame, text="0")  # Значение ползунка
        self.size_value.grid(row=2, column=2, padx=5, pady=5)

        self.mass_label = ttk.Label(self.control_frame, text="Масса")
        self.mass_label.grid(row=3, column=0, sticky="w", padx=5, pady=5)

        self.mass_slider = ttk.Scale(self.control_frame, from_=0, to_=100, orient="horizontal")
        self.mass_slider.grid(row=3, column=1, padx=5, pady=5)
        self.mass_value = ttk.Label(self.control_frame, text="0")  # Значение ползунка
        self.mass_value.grid(row=3, column=2, padx=5, pady=5)

        self.frequency_label = ttk.Label(self.control_frame, text="Кол-во частиц")
        self.frequency_label.grid(row=4, column=0, sticky="w", padx=5, pady=5)

        self.frequency_slider = ttk.Scale(self.control_frame, from_=0, to_=100, orient="horizontal")
        self.frequency_slider.grid(row=4, column=1, padx=5, pady=5)
        self.frequency_value = ttk.Label(self.control_frame, text="0")  # Значение ползунка
        self.frequency_value.grid(row=4, column=2, padx=5, pady=5)

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

        # Привязываем событие обновления значения
        self.temperature_slider.bind("<Motion>", lambda event: self.update_slider_value(event, self.temperature_value, self.temperature_slider))
        self.viscosity_slider.bind("<Motion>", lambda event: self.update_slider_value(event, self.viscosity_value, self.viscosity_slider))
        self.size_slider.bind("<Motion>", lambda event: self.update_slider_value(event, self.size_value, self.size_slider))
        self.mass_slider.bind("<Motion>", lambda event: self.update_slider_value(event, self.mass_value, self.mass_slider))
        self.frequency_slider.bind("<Motion>", lambda event: self.update_slider_value(event, self.frequency_value, self.frequency_slider))

# The commented out method `update_slider_value` in the code is a function that updates the text
# displayed on a label widget based on the current value of a slider widget. It takes three
# parameters: `event`, `label`, and `slider`.
    # def update_slider_value(self, event, label, slider):
    #     label.config(text=f"{int(slider.get())}")  # Обновление текста метки

    def apply_settings(self):
        # Получение значений ползунков
        settings = {
            "temperature": self.temperature_slider.get(),
            "viscosity": self.viscosity_slider.get(),
            "size": self.size_slider.get(),
            "mass": self.mass_slider.get(),
            "frequency": self.frequency_slider.get(),
        }
        # Отправляем настройки на сервер и записываем их в JSON
        self.client.send_settings(settings)
        self.log_text.insert(tk.END, "Настройки отправлены на сервер и сохранены в файл.\n")
        

    def reset_settings(self):
        # Сброс настроек
        self.log_text.insert(tk.END, "Параметры сброшены\n")
        self.temperature_slider.set(0)
        self.viscosity_slider.set(0)
        self.size_slider.set(0)
        self.mass_slider.set(0)
        self.frequency_slider.set(0)

    def start_simulation(self):
        self.client.connect()
        self.log_text.insert(tk.END, "Запуск симуляции\n")


        # Запуск потока для получения координат
        threading.Thread(target=self.client.receive_coordinates, daemon=True).start()

    def stop_simulation(self):
        self.client.close()
        self.log_text.insert(tk.END, "Симуляция остановлена\n")

    def update_plot(self, coordinates):
        """Обновление 3D-графика."""
        if coordinates:
            self.ax.clear()
            self.ax.scatter(coordinates[0], coordinates[1], coordinates[2])
            self.canvas.draw()
    def on_closing(self):
        """Обработка закрытия окна."""
        self.client.close()
        self.destroy()

# Основная логика для запуска приложения
if __name__ == "__main__":
    client = Client()
    gui = SimulationGUI(client)
    gui.mainloop()
