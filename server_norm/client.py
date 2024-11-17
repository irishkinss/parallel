import socket

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

    def send_command(self, command):
        """Отправка команды на сервер."""
        if self.connected:
            self.client_socket.sendall(command.encode())
            print(f"Sent command: {command}")
        else:
            print("Not connected to server.")

    def close(self):
        """Закрытие соединения с сервером."""
        if self.client_socket:
            self.client_socket.close()
            print("Connection closed.")

if __name__ == "__main__":
    client = Client()
    client.connect()
    client.send_command("start")
    client.close()

