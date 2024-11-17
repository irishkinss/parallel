import socket
from gui import SimulationGUI

def check_server(server_host='127.0.0.1', server_port=12345):
    """Проверка, запущен ли сервер."""
    try:
        with socket.create_connection((server_host, server_port), timeout=2):
            return True
    except (socket.timeout, socket.error):
        return False

if __name__ == "__main__":
    if check_server():
        app = SimulationGUI()
        app.mainloop()
    else:
        print("Не удалось подключиться к серверу. Приложение не будет запущено.")

