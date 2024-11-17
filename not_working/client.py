import socket

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = None
        self.connected = False

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
            self.connected = True
        except socket.error:
            print("Не удалось подключиться к серверу.")

    def send_command(self, command):
        if self.connected:
            self.client_socket.sendall(command.encode())

    def close(self):
        if self.client_socket:
            self.client_socket.close()
            self.connected = False

