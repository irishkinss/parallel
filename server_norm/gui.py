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
        
    def log_message(message):
        log_text.insert(tk.END, f"{message}\n")
        log_text.see(tk.END)
    def apply_settings():
        log_message("Применить настройки")

    def reset_settings():
        log_message("Сбросить настройки")

    def start_simulation():
        log_message("Симуляция началась")

    def pause_simulation():
        log_message("Симуляция приостановлена")

    def stop_simulation():
        log_message("Симуляция остановлена")



    def start_window():
        # Создание главного окна
        root = tk.Tk()
        root.title("Симуляция броуновского движения")

        # Основная рамка
        main_frame = ttk.Frame(root, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Параметры среды
        params_frame = ttk.LabelFrame(main_frame, text="Параметры эмуляции", padding=10)
        params_frame.grid(row=0, column=1, padx=10, pady=10, sticky="n")

        labels = ["Температура", "Вязкость", "Размер", "Масса", "Кол-во частиц"]
        sliders = {}

        for i, label_text in enumerate(labels):
            label = ttk.Label(params_frame, text=label_text)
            label.grid(row=i, column=0, sticky="w")
            slider = ttk.Scale(params_frame, from_=0, to=100, orient="horizontal")
            slider.grid(row=i, column=1, sticky="ew", pady=2)
            sliders[label_text] = slider

        # Управление
        buttons_frame = ttk.Frame(params_frame, padding=10)
        buttons_frame.grid(row=len(labels), column=0, columnspan=2, pady=10)

        apply_button = ttk.Button(buttons_frame, text="Применить", command=apply_settings)
        apply_button.grid(row=0, column=0, padx=5)

        reset_button = ttk.Button(buttons_frame, text="Сбросить", command=reset_settings)
        reset_button.grid(row=0, column=1, padx=5)

        # Элементы управления симуляцией
        sim_frame = ttk.LabelFrame(main_frame, text="Управление эмуляцией", padding=10)
        sim_frame.grid(row=1, column=1, padx=10, pady=10, sticky="n")

        start_button = ttk.Button(sim_frame, text="Запуск", command=start_simulation)
        start_button.grid(row=0, column=0, padx=5)

        pause_button = ttk.Button(sim_frame, text="Пауза", command=pause_simulation)
        pause_button.grid(row=0, column=1, padx=5)

        stop_button = ttk.Button(sim_frame, text="Стоп", command=stop_simulation)
        stop_button.grid(row=0, column=2, padx=5)

        # Лог
        log_frame = ttk.Frame(main_frame, padding=10)
        log_frame.grid(row=2, column=0, columnspan=2, sticky="ew")

        log_label = ttk.Label(log_frame, text="Лог:")
        log_label.grid(row=0, column=0, sticky="w")

        log_text = tk.Text(log_frame, height=10, wrap="word")
        log_text.grid(row=1, column=0, sticky="nsew")

        # Настройки сетки
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Создаем виджет для 3D-графика
        fig = plt.figure()
        self.ax = fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.start_button = tk.Button(self, text="Start Simulation", command=self.start_simulation)
        self.start_button.pack()

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
    
    def start_simulation(self):
        viscosity = float(self.viscosity_entry.get())
        temperature = float(self.temperature_entry.get())
        dt = float(self.dt_entry.get())

        # Передайте параметры в класс Simulation
        particles = [Particle(random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1), 0.01, 1.0, temperature) for _ in range(100)]
        simulation = Simulation(particles, viscosity, temperature, dt)
        simulation.run()

if __name__ == "__main__":
    client = Client()
    gui = SimulationGUI(client)
    gui.protocol("WM_DELETE_WINDOW", gui.on_closing)
    gui.mainloop()