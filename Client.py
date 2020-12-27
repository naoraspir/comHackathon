from struct import *
from socket import *
import enum

HOST = gethostname()
localPORT = 13117
buffer_size = 2048


class ClientState(enum.Enum):
    searching = 1
    connecting = 2
    game_mode = 3


class Client:
    def __init__(self):
        self.team_name = "Mr. & Ms. Dor"
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.tcp_socket = socket(AF_INET, SOCK_STREAM)

        self.state = ClientState.searching

    def connect_to_server(self, server_address):
        self.tcp_socket.connect(server_address)


    def look_for_server(self):
        while True:
            message, server_address = self.udp_socket.recvfrom(buffer_size)
            print(f'Received offer from {server_address}, attempting to connect...')

            print(f'DEBUG: Server message: {message}')
            print(f'DEBUG: Server IP: {server_address}')
            self.state = ClientState.connecting
            self.connect_to_server(server_address)




