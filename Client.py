import struct
import time
import traceback
from struct import *
from socket import *
import enum
from msvcrt import getch
from threading import Thread
import keyboard

CLIENT_IP = gethostbyname(gethostname())
localPORTUDP = 13117
localPORTTCP = 2081  # todo switch back to 2080
buffer_size = 1024


class Client:
    def __init__(self):
        self.team_name = "Spam Tov Heavy"
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.tcp_socket = socket(AF_INET, SOCK_STREAM)
        self.in_play = False

    def connect_to_server(self, server_adress, server_port):
        self.tcp_socket.bind(('',localPORTTCP))
        self.tcp_socket.connect((server_adress, server_port))

    def send_name(self):
        msg = self.team_name + '\n'
        self.tcp_socket.send(msg.encode())

    def look_for_server(self):

        self.udp_socket.bind((CLIENT_IP, localPORTUDP))
        # connecting and sending name.
        while True:
            try:
                buffer_m, server_address = self.udp_socket.recvfrom(buffer_size)
                data_tuple = struct.unpack('Ibh', buffer_m)
                M_Cookie = data_tuple[0]
                M_type = data_tuple[1]
                server_port = data_tuple[2]
                if M_Cookie != 0xfeedbeef or M_type != 0x2:
                    continue
                print(f'Received offer from {server_address[0]}, attempting to connect...')
                self.connect_to_server(server_address[0], server_port)
                try:
                    self.send_name()
                except:
                    traceback.print_exc()
                    self.tcp_socket.close()
                    continue
                break
            except:
                traceback.print_exc()
                print("there was an excpetion, finding another server")
                continue
        self.udp_socket.close()

    def keyboard_recorder(self):
        print("trying to record")
        counter=0
        keyboard.on_press(self.send_to_server)
        while self.in_play:
            continue
        print(counter)

    def send_to_server(self, event):
        try:
            self.tcp_socket.send(event.name.encode())
        except:
            return
    def game_play(self):
        try:
            record_trd = Thread(target=self.keyboard_recorder)
            msg = self.tcp_socket.recv(2048).decode()
            print(msg)  # game started
            self.in_play = True
            record_trd.start()
            msg = self.tcp_socket.recv(2048).decode()
            self.in_play = False
            record_trd.join()
            print(msg)  # game ended
            print("Server disconnected, listening for offer requests...")
            self.tcp_socket.close()
            return
        except:
            # traceback.print_exc()
            self.crash()
            return

    def crash(self):
        self.tcp_socket.close()


print("Client started, listening for offer requests...")
while 1:
    client = Client()
    client.look_for_server()
    client.game_play()
