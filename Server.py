import enum
import time
from socket import *
from threading import *
import struct

SERVER_PORT = 2080
SERVER_IP = gethostbyname(gethostname())


class ServerState(enum.Enum):
    waiting_for_clients = 1
    game_mode = 2


class Server:
    def __init__(self):
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.tcp_socket = socket(AF_INET, SOCK_STREAM)
        self.state = ServerState.waiting_for_clients
        self.connections = {}
        

    def send_broadcast_messages(self):
        message_to_send = struct.pack('Ibh', 0xfeedbeef, 0x2, 0x820)
        send_until = time.time() + 10
        while time.time() < send_until:
            self.udp_socket.sendto(message_to_send, ('<broadcast>', 13117))
            time.sleep(1)

    def waiting_for_clients(self):
        """
            This function sends UDP broadcast messages each 1 sec
            for 10 seconds and listening for clients responses.
        """
        self.udp_socket.bind(('', SERVER_PORT))
        print(f'Server started, listening on IP address {SERVER_IP}')

        broadcast_thread = Thread(target=self.send_broadcast_messages())
        broadcast_thread.start()
        self.tcp_socket.settimeout(0.2)
        while broadcast_thread.isAlive():
            try:
                client_socket, address = self.tcp_socket.accept()
                self.connections[address] = client_socket
            except:
                continue
        
        self.udp_socket.close()

    def game_play(self, client_socket, address):
            pass


server = Server()
server.waiting_for_clients()
