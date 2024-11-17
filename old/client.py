# client.py
import socket
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import threading
from tkinter import Tk, Button, Frame
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Настройки для подключения к серверу
server_address = ('localhost', 65432)
num_particles = 100
cube_size = 5.0

# Глобальные переменные для управления состоянием симуляции
positions = np.zeros((num_particles, 3))
velocities = np.zeros((num_particles, 3))  # Для хранения скоростей частиц
is_running = False  # Изначально симуляция остановлена

# Получение данных о частицах от сервера
def receive_data():
    global positions, velocities
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(server_address)
        while True:
            if is_running:
                # Ожидание точного количества данных
                data = b''
                while len(data) < num_particles * 6 * 8:  # Теперь учитываем и позиции, и скорости
                    packet = client_socket.recv(num_particles * 6 * 8 - len(data))
                    if not packet:
                        break
                    data += packet

                # Проверка, что пришло ровно нужное количество данных
                if len(data) == num_particles * 6 * 8:
                    array_data = np.frombuffer(data, dtype=np.float64).reshape(num_particles, 6)
                    positions = array_data[:, :3]
                    velocities = array_data[:, 3:6]

# Функции для управления запуском и остановкой симуляции
def start_simulation():
    global is_running
    is_running = True

def stop_simulation():
    global is_running
    is_running = False

# GUI для 3D-визуализации движения частиц
def start_gui():
    root = Tk()
    root.title("Симуляция Броуновского движения")

    # Создание холста для графического интерфейса
    frame = Frame(root)
    frame.pack(side="top")

    # Создание кнопок управления внизу окна
    control_frame = Frame(root)
    control_frame.pack(side="bottom")

    start_button = Button(control_frame, text="Запуск", command=start_simulation)
    start_button.pack(side="left")

    stop_button = Button(control_frame, text="Стоп", command=stop_simulation)
    stop_button.pack(side="right")

    # Создание 3D-графика с использованием Matplotlib
    fig = plt.Figure(figsize=(6, 6), dpi=100)
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlim([-cube_size / 2, cube_size / 2])
    ax.set_ylim([-cube_size / 2, cube_size / 2])
    ax.set_zlim([-cube_size / 2, cube_size / 2])
    scatter = ax.scatter(positions[:, 0], positions[:, 1], positions[:, 2])

    # Функция для плавного обновления частиц
    def update(frame):
        if is_running:
            scatter._offsets3d = (positions[:, 0], positions[:, 1], positions[:, 2])
        return scatter,

    # Встраиваем график в tkinter
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack()

    # Запуск анимации с использованием FuncAnimation
    ani = FuncAnimation(fig, update, interval=50, blit=False)

    root.mainloop()

# Запуск потоков для получения данных, визуализации и интерфейса управления
receive_thread = threading.Thread(target=receive_data, daemon=True)
receive_thread.start()

start_gui()

