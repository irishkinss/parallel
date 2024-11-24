import socket
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import ast
import json
from gui import SimulationGUI
import time

class Client:
    def __init__(self, server_host='127.0.0.2', server_port=12345, gui = None):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = None
        self.connected = False
        self.gui = gui
        self.running = False
        self.receive_thread = None

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
        try:
            # Установка тайм-аута для получения
            self.client_socket.settimeout(10)
            
            # Получение данных
            data = self.client_socket.recv(4096).decode('utf-8')
            print(f"[DEBUG] Полученные сырые данные (первые 100 символов): {data[:100]}")  # Debugging
            
            if data:
                try:
                    # Попытка распарсить JSON
                    coordinates = json.loads(data)
                    print(f"[DEBUG] Тип данных coordinates: {type(coordinates)}")
                    print(f"[DEBUG] Количество частиц: {len(coordinates)}")
                    if len(coordinates) > 0:
                        print(f"[DEBUG] Пример первой частицы: {coordinates[0]}")
                    
                    # Проверяем структуру данных
                    if isinstance(coordinates, list):
                        # Если координаты уже в нужном формате
                        if all(isinstance(coord, list) or isinstance(coord, tuple) for coord in coordinates):
                            print(f"[DEBUG] Получены корректные координаты {len(coordinates)} частиц")
                            
                            # Преобразуем все кортежи в списки для единообразия
                            coordinates = [list(coord) if isinstance(coord, tuple) else coord for coord in coordinates]
                            
                            # Вызываем метод update_plot в GUI
                            if self.gui:
                                print("[DEBUG] Вызов update_plot с координатами")
                                self.gui.update_plot(coordinates)
                            else:
                                print("[ERROR] GUI объект не инициализирован")
                            
                            return coordinates
                        else:
                            print("[ERROR] Неверный формат координат")
                            return None
                    else:
                        print("[ERROR] Координаты не в виде списка")
                        return None
                
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Ошибка декодирования JSON: {e}")
                    print(f"[ERROR] Полученные данные: {data}")
                    return None
            else:
                print("[WARNING] Получены пустые данные")
                return None
                
        except socket.timeout:
            print("[ERROR] Таймаут при получении данных")
            return None
        except Exception as e:
            print(f"[ERROR] Неожиданная ошибка: {e}")
            return None

    def start_receiving(self):
        """Запуск получения координат от сервера."""
        print("[DEBUG] Запуск получения координат")
        while self.running:
            try:
                coordinates = self.receive_coordinates()
                if coordinates:
                    if self.gui:
                        self.gui.update_plot(coordinates)
                else:
                    print("[WARNING] Получены пустые координаты")
                    break
            except Exception as e:
                print(f"[ERROR] Ошибка при получении координат: {e}")
                break
        print("[DEBUG] Завершение цикла получения координат")

    def start_simulation(self):
        """Запуск потока получения координат"""
        # Остановим предыдущую симуляцию, если она запущена
        if self.running or self.receive_thread:
            self.stop_simulation()
            time.sleep(0.1)  # Даем время на закрытие соединения
        
        # Подключаемся к серверу
        if not self.connect():
            print("[ERROR] Не удалось подключиться к серверу")
            return False
            
        # Загружаем последние настройки из файла
        try:
            with open('settings.json', 'r') as file:
                settings = json.load(file)
                # Отправляем настройки серверу
                if not self.send_settings(settings):
                    print("[ERROR] Не удалось отправить настройки")
                    self.stop_simulation()
                    return False
        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке настроек: {e}")
            self.stop_simulation()
            return False

        # Устанавливаем флаг и запускаем поток
        self.running = True
        self.receive_thread = threading.Thread(target=self.start_receiving)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        return True

    def stop_simulation(self):
        """Остановка потока получения координат."""
        print("[DEBUG] Остановка симуляции")
        # Сначала сбрасываем флаг
        self.running = False
        
        # Закрываем сокет
        if self.client_socket:
            try:
                self.client_socket.close()
                self.client_socket = None
                self.connected = False
            except Exception as e:
                print(f"[ERROR] Ошибка при закрытии сокета: {e}")
        
        # Ждем завершения потока
        if self.receive_thread and self.receive_thread.is_alive():
            try:
                self.receive_thread.join(timeout=1.0)
            except Exception as e:
                print(f"[ERROR] Ошибка при ожидании завершения потока: {e}")
            self.receive_thread = None
            
        print("[DEBUG] Симуляция остановлена")

    def update_plot(self, coordinates):
        """Обновление графика с новыми координатами."""
        self.ax.clear()
        xs, ys, zs = zip(*coordinates)
        self.ax.scatter(xs, ys, zs)
        self.canvas.draw()

    def close(self):
        """Закрытие соединения с сервером"""
        self.stop_simulation()
        if self.client_socket:
            self.client_socket.close()
            print("Connection closed.")

if __name__ == "__main__":
    client = Client()
    gui = SimulationGUI(client)
    # Устанавливаем GUI объект в клиенте
    client.gui = gui
    gui.protocol("WM_DELETE_WINDOW", gui.on_closing)
    gui.mainloop()