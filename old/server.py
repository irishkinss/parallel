# server.py
import socket
import threading
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# Настройки симуляции
num_particles = 30
particles_per_thread = 10  # Общее количество потоков = num_particles / particles_per_thread
cube_size = 5.0
collision_radius = 0.2  # Минимальное расстояние для столкновения
dt = 0.05  # Временной шаг

# Параметры частиц (позиция, скорость)
positions = np.random.uniform(-cube_size / 2, cube_size / 2, (num_particles, 3))
velocities = np.random.normal(0, 1, (num_particles, 3))

# Настройки сети
server_address = ('localhost', 65432)
client_connections = []

# Функция для расчёта движения частиц в потоке
def update_particle_positions(start_idx, end_idx):
    global positions, velocities
    for i in range(start_idx, end_idx):
        # Перемещение частицы на основе текущей скорости
        positions[i] += velocities[i] * dt

# Функция для перерасчета столкновений
def handle_collisions_and_boundaries():
    global positions, velocities
    for i in range(num_particles):
        # Проверка столкновений с границами куба
        for dim in range(3):
            if positions[i, dim] >= cube_size / 2 or positions[i, dim] <= -cube_size / 2:
                velocities[i, dim] *= -1  # Отражение от стенки

        # Проверка столкновений с другими частицами
        for j in range(i + 1, num_particles):
            distance = np.linalg.norm(positions[i] - positions[j])
            if distance < collision_radius:
                velocities[i], velocities[j] = velocities[j], velocities[i]  # Обмен скоростей

# Основной цикл расчётов с многопоточностью
def calculate_positions():
    with ThreadPoolExecutor(max_workers=num_particles // particles_per_thread) as executor:
        while True:
            # Запускаем обновление частиц в потоках
            futures = []
            for i in range(0, num_particles, particles_per_thread):
                futures.append(executor.submit(update_particle_positions, i, i + particles_per_thread))

            # Ждем, пока все потоки завершатся
            for future in futures:
                future.result()

            # Проверяем столкновения и отражение от стенок
            handle_collisions_and_boundaries()

# Поток для отправки данных клиентам
def broadcast_positions():
    global positions, velocities
    while True:
        data = np.hstack((positions, velocities)).tobytes()
        for conn in client_connections:
            try:
                conn.sendall(data)
            except:
                client_connections.remove(conn)

# Основной серверный процесс
def server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(server_address)
        server_socket.listen()
        print("Сервер запущен и ожидает подключений...")

        # Обработка подключений клиентов
        while True:
            conn, addr = server_socket.accept()
            client_connections.append(conn)
            print(f"Подключен клиент: {addr}")

# Запуск многопоточных расчетов и передачи данных
calculation_thread = threading.Thread(target=calculate_positions, daemon=True)
broadcast_thread = threading.Thread(target=broadcast_positions, daemon=True)
server_thread = threading.Thread(target=server, daemon=True)

calculation_thread.start()
broadcast_thread.start()
server_thread.start()

# Основной поток будет ожидать завершения других потоков
calculation_thread.join()
broadcast_thread.join()
server_thread.join()

