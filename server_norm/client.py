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
                
                # Проверяем валидность данных
                if not coordinates or not isinstance(coordinates, list):
                    continue
                    
                # Проверяем наличие всех необходимых координат
                valid_coordinates = []
                for coord in coordinates:
                    if all(key in coord for key in ['x', 'y', 'z']):
                        valid_coordinates.append(coord)
                
                # Обновляем график только если есть валидные координаты
                if valid_coordinates and self.gui:
                    self.gui.update_plot(valid_coordinates)
                    
                # Подтверждаем получение данных
                try:
                    self.client_socket.sendall(b'ACK')
                except:
                    pass
                    
            except Exception as e:
                print(f"Ошибка при получении данных: {e}")
                if not self.running:
                    break
                time.sleep(0.1)  # Небольшая задержка перед следующей попыткой
        
        # Если вышли из цикла, закрываем соединение
        self.connected = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass

    def update_plot(self, coordinates):
        """Обновление графика через GUI"""
        if self.gui:
            self.gui.update_plot(coordinates)

    def start_simulation(self):
        """Запуск симуляции"""
        try:
            if not self.connected:
                if not self.connect():
                    print("Не удалось подключиться к серверу")
                    return False

            self.running = True
            # Запускаем поток для получения данных
            self.receive_thread = threading.Thread(target=self.start_receiving)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            print("Симуляция запущена")
            return True
            
        except Exception as e:
            print(f"Ошибка при запуске симуляции: {e}")
            self.running = False
            return False

    def stop_simulation(self):
        """Остановка симуляции"""
        try:
            self.running = False
            if self.receive_thread:
                self.receive_thread.join(timeout=1.0)
                self.receive_thread = None
                
            if self.client_socket:
                try:
                    # Отправляем команду остановки
                    self.client_socket.sendall(b'STOP')
                    print("Команда остановки отправлена")
                except:
                    pass
                    
            print("Симуляция остановлена")
            return True
            
        except Exception as e:
            print(f"Ошибка при остановке симуляции: {e}")
            return False

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