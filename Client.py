import struct
import time
import traceback
from struct import *
import socket
from scapy.all import *
#import getch
from threading import Thread
import keyboard
from select import select
import sys
import os

CLIENT_IP = get_if_addr('eth1')
localPORTUDP = 13117
localPORTTCP = 2080 
buffer_size = 1024
BROAD_NET = '172.1.255.255'



class Client:
    def __init__(self):
        self.team_name = "Spam Tov Heavy"
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.in_play = False

    def connect_to_server(self, server_adress, server_port):
        """
            meathod used for connecting to specified server.
            params: 
                server_adress 
                server_port
        """
        self.tcp_socket.connect((server_adress, server_port))

    def send_name(self):
        """
            meathod used for sending team name to connected server server.
        """
        msg = self.team_name + '\n'
        self.tcp_socket.send(msg.encode())

    def look_for_server(self):
        """
            meathod used for looking for servers to play with.
        """
        self.udp_socket.bind((BROAD_NET, localPORTUDP))
        # connecting and sending name.
        while True:
            try:
                buffer_m, server_address = self.udp_socket.recvfrom(buffer_size)
                print('\x1b[6;30;42m' + 'Packet recived: '+ str(buffer_m) + '\x1b[0m')

                print('\x1b[6;30;42m' + 'address recieved : '+str(server_address) + '\x1b[0m')
                try:
                    #recieve and unpack msg from server over udp.
                    data_tuple = struct.unpack('Ibh', buffer_m)
                    print('\x1b[6;30;45m' + 'data translated: '+str(data_tuple) + '\x1b[0m')
                except:
                    time.sleep(1)
                    continue
                M_Cookie = data_tuple[0]
                M_type = data_tuple[1]
                server_port = data_tuple[2]
                
                #check if the msg is with the cookie and type agreed by client and server.
            
                if M_Cookie != 0xfeedbeef and M_type != 0x2:
                    continue
                #connect to server.
                print('\x1b[6;30;43m' + f'Received offer from {server_address[0]}, attempting to connect...' + '\x1b[0m')

                self.connect_to_server(server_address[0], server_port)
                
                #send team name.
                try:
                    self.send_name()
                except:
                    self.tcp_socket.close()
                    continue
                break

            except:
                time.sleep(3)
                continue

        #done with udp connection, close.   
        self.udp_socket.close()

    def keyboard_recorder(self):
        """
            thread meathod used for recording and sending pressed keys from client to server while in game.  
        """

        # set the system settings for reading chars without blocking.
        os.system("stty raw -echo")

        #while in game read pressed key and send to server over tcp socket.
        while self.in_play:
            #set time out for last loop, withour this the loop will have to recieve an extra key press to end.
            data, a, b = select([sys.stdin],[],[],0)
            if data:
                #read press.
                character = sys.stdin.read(1)
                #send press to server
                self.send_to_server(character)
            
        #return system setting to normal
        os.system("stty -raw echo")

    def send_to_server(self, event):
        """
            meathod used for sending pressed key to connected server.
            params: 
                event - the key pressed by client to send.
        """
        try:
            self.tcp_socket.send(event.encode())
        except:
            return
   
    def game_play(self):
        """
            meathod used for game play logic.
        """
        try:
            #open key press thread
            record_trd = Thread(target=self.keyboard_recorder)
            
            #recieving the first start game message
            msg = self.tcp_socket.recv(2048).decode()

            print(msg)
            #set client state to in game state.
            self.in_play = True
            record_trd.start()

            #recieving the Game Over message
            msg = self.tcp_socket.recv(2048).decode()
            self.in_play = False
            record_trd.join()

            # game ended    
            print(msg)  
            
            print('\x1b[6;30;42m' + 'Server disconnected, listening for offer requests...' + '\x1b[0m')

            self.tcp_socket.close()
        except:
            self.crash()
            return
        #close all ports
        self.crash()

    def crash(self):
        """
            in case needed, close all open sockets. 
        """
        self.tcp_socket.close()


print('\x1b[6;30;44m' + 'Client started, listening for offer requests...' + '\x1b[0m')

while 1:
    client = Client()
    client.look_for_server()
    client.game_play()
    time.sleep(0.05)
