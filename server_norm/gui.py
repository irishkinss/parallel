import tkinter as tk
from tkinter import ttk
import socket
from client import Client  # Импортируем клиентскую часть
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # Импортируем 3D-проекцию

class SimulationGUI(tk.Tk):
    def __init__(self, server_host='127.0.0.1', server_port=12345):
        super().__init__()
        self.title("3D Brownian Motion Simulation")
        self.geometry("800x600")
        
        self.client = Client(server_host, server_port)
        self.client.connect()

        # Создаем виджет для 3D-графика слева
        fig = Figure(figsize=(5, 5), dpi=100)
        self.ax = fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Панель для ввода параметров справа
        params_frame = tk.Frame(self)
        params_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Поля ввода для параметров
        self.create_parameter_field(params_frame, "Температура", "300")
        self.create_parameter_field(params_frame, "Вязкость", "0.001")
        self.create_parameter_field(params_frame, "Частицы", "50")
        self.create_parameter_field(params_frame, "Масса", "1")
        self.create_parameter_field(params_frame, "Радиус", "0.1")
        self.create_parameter_field(params_frame, "Объем куба", "10")
        self.params["Скорость анимации (dt)"] = self.create_parameter_field(params_frame, "Скорость анимации (dt)", "0.01")

        # Кнопки управления
        start_button = tk.Button(params_frame, text="Запуск", command=self.start_simulation)
        start_button.pack(fill=tk.X, pady=5)
        
        pause_button = tk.Button(params_frame, text="Пауза", command=self.pause_simulation)
        pause_button.pack(fill=tk.X, pady=5)
        
        stop_button = tk.Button(params_frame, text="Стоп", command=self.stop_simulation)
        stop_button.pack(fill=tk.X, pady=5)
        
        # Проверка наличия сервера при старте
        self.check_server_status()

    def create_parameter_field(self, frame, label, default_value):
        label = tk.Label(frame, text=label)
        label.pack()
        entry = tk.Entry(frame)
        entry.insert(0, default_value)
        entry.pack(fill=tk.X, padx=5, pady=5)
    
    def start_simulation(self):
        """Запуск симуляции через сервер."""
        if not self.client.connected:
            print("Нет подключения к серверу!")
            return

        # Отправляем команду серверу для старта
        self.client.send_command("start")
        print("Starting simulation...")

    def pause_simulation(self):
        """Пауза симуляции через сервер.""" 
        if not self.client.connected:
            print("Нет подключения к серверу!")
            return

        # Отправляем команду серверу для паузы
        self.client.send_command("pause")
        print("Pausing simulation...")

    def stop_simulation(self):
        """Остановка симуляции через сервер."""
        if not self.client.connected:
            print("Нет подключения к серверу!")
            return

        # Отправляем команду серверу для остановки
        self.client.send_command("stop")
        print("Stopping simulation...")

    def check_server_status(self):
        """Проверка доступности сервера."""
        if self.client.connected:
            print("Подключение к серверу установлено.")
        else:
            print("Не удалось подключиться к серверу.")
    
    def on_close(self):
        """Обработчик закрытия окна для корректной остановки клиента."""
        if self.client.connected:
            self.client.close()  # Отключаемся от сервера
        self.quit()  # Закрываем окно приложения

if __name__ == "__main__":
    app = SimulationGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_close)  # Используем on_close при закрытии окна
    app.mainloop()

