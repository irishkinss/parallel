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
    def __init__(self, server_host='127.0.0.2', server_port=12345):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = None
        self.connected = False
        self.running = False
        self.receive_thread = None
        self.gui = None  # Ссылка на GUI

    def set_gui(self, gui):
        """Установка ссылки на GUI"""
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
        """Отправка настроек на сервер"""
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

    def receive_message(self):
        """Получение полного сообщения от сервера"""
        try:
            # Получаем размер сообщения
            size_data = self.client_socket.recv(4)
            if not size_data or len(size_data) != 4:
                return None
                
            msg_size = int.from_bytes(size_data, byteorder='big')
            
            # Получаем само сообщение
            chunks = []
            bytes_received = 0
            
            while bytes_received < msg_size:
                chunk = self.client_socket.recv(min(msg_size - bytes_received, 4096))
                if not chunk:
                    return None
                chunks.append(chunk)
                bytes_received += len(chunk)
            
            return b''.join(chunks).decode()
            
        except Exception as e:
            print(f"Ошибка при получении сообщения: {e}")
            return None

    def start_receiving(self):
        """Получение координат от сервера"""
        while self.running:
            try:
                # Получаем данные
                data = self.receive_message()
                if not data:
                    print("Соединение закрыто сервером")
                    break

                # Парсим JSON
                coordinates = json.loads(data)
                
                # Преобразуем в формат для отображения
                display_coords = [(p['x'], p['y'], p['z']) for p in coordinates]
                
                # Обновляем график через GUI
                self.update_plot(display_coords)
                
                # Отправляем подтверждение
                try:
                    self.client_socket.send(b'ACK')
                except:
                    print("Ошибка отправки подтверждения")
                    break

            except json.JSONDecodeError as e:
                print(f"Ошибка декодирования JSON: {e}")
                continue
            except Exception as e:
                print(f"Ошибка при получении координат: {e}")
                break

        print("Поток получения координат завершен")
        self.running = False

    def update_plot(self, coordinates):
        """Обновление графика через GUI"""
        if self.gui:
            self.gui.update_plot(coordinates)

    def start_simulation(self):
        """Запуск потока получения координат"""
        try:
            # Останавливаем предыдущую симуляцию, если она запущена
            if self.running:
                self.stop_simulation()
                time.sleep(0.1)  # Даем время на остановку

            # Запускаем поток получения данных
            self.running = True
            self.receive_thread = threading.Thread(target=self.start_receiving)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            print("Симуляция запущена")
            return True

        except Exception as e:
            print(f"Ошибка при запуске симуляции: {e}")
            return False

    def stop_simulation(self):
        """Остановка потока получения координат"""
        try:
            self.running = False
            if self.receive_thread and self.receive_thread.is_alive():
                self.receive_thread.join(timeout=1.0)
            print("Симуляция остановлена")
        except Exception as e:
            print(f"Ошибка при остановке симуляции: {e}")

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
    client.set_gui(gui)
    gui.root.protocol("WM_DELETE_WINDOW", gui.on_closing)
    gui.root.mainloop()