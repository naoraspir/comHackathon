from struct import *
from socket import *
import enum

HOST = gethostname()
localPORTUDP = 13117
localPORTTCP= 2080
buffer_size = 7


class ClientState(enum.Enum):
    searching = 1
    connecting = 2
    game_mode = 3


class Client:
    def __init__(self):
        self.team_name = "Spam Tov Heavy"
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.tcp_socket = socket(AF_INET, SOCK_STREAM)

    def connect_to_server(self, server_port):
        self.tcp_socket.connect(("",server_port))

    def send_name(self):
        self.tcp_socket.send(self.team_name+"\n")

    def look_for_server(self):
        print("Client started, listening for offer requests...")
        self.udp_socket.bind("",localPORTUDP)
        #connecting and sending name.
        while True:
            try:
                buffer_m, server_address = self.udp_socket.recvfrom(buffer_size)
                data_tuple = struct.unpack('Ibh', buffer_m)
                M_Cookie= data_tuple(0)
                M_type= data_tuple(1)
                server_port = data_tuple(2)
                if M_Cookie != 0xfeedbeef or M_type != 0x2:
                    continue
                print(f'Received offer from {server_address}, attempting to connect...')
                self.connect_to_server(server_port)
                self.send_name()
                break
            except:
                continue
        #





