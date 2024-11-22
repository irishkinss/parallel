import threading
import time
from server import Server  # Импортируем класс Server из server.py
from gui import SimulationGUI  # Импортируем класс SimulationGUI из gui.py
from client import Client  # Импортируем класс Client из client.py

def run_server():
    server = Server()
    server.start()

def run_client():
    client = Client()
    gui = SimulationGUI(client)
    gui.protocol("WM_DELETE_WINDOW", gui.on_closing)
    gui.mainloop()

if __name__ == "__main__":
    # Запускаем сервер в отдельном потоке
    server_thread = threading.Thread(target=run_server)
    server_thread.start()

    # Даем серверу немного времени для инициализации
    time.sleep(1)

    # Запускаем клиент
    run_client()

    # Ждем завершения потока сервера
    server_thread.join()