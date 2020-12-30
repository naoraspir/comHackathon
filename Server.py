import enum
import time
import traceback
import socket
from threading import *
import struct
from scapy.all import *
from select import select

SERVER_PORT = 2080
SERVER_IP = get_if_addr('eth1')


class Server:
    def __init__(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.connections = {}
        self.game_treads = {}
        self.group1 = {}
        self.group2 = {}

    def send_broadcast_messages(self, udp_socket):
        """
            meathod used for sending udp broadcast messagges.
            params: 
                udp_socket - the server udp socket.
        """
        #packing the udp in Ibn format including coockie,type,SErver port.
        message_to_send = struct.pack('Ibh', 0xfeedbeef, 0x2, SERVER_PORT)

        send_until = time.time() + 10
        #starting a while loop that will run for 10 seconds.
        while time.time() <= send_until:
            #send the udp packet on broadcast.
            udp_socket.sendto(message_to_send, ('<broadcast>', 13114))
            time.sleep(1)

    def accept_conn(self, broadcast_thread, tcp_socket):
        """
            thread used for accepting clients connections that are sent and their team name. works simultanious with the udp broadcast.
            params: 
                broadcast_thread - udp broadcast thread, use to know when the server needs to stop accepting new clients for game.
                tcp_socket - main server tcp socket, used to accept client requests.
        """
        #while the server is broadcasting accept new clients, recieve their name and connection and add them to server connections dictionary field.
        while broadcast_thread.is_alive():
            try:
                client_socket, address = tcp_socket.accept()
                group_name = client_socket.recv(2048).decode()
                print(f'team {group_name} has connected succsesfuly')
                self.connections[group_name] = {"client_socket": client_socket, "address": address}
            except :
                continue

    def waiting_for_clients(self):
        """
            meathod used for the whole clients offering and connecting stage.
            the broadcast msg will be sent every second for 10 seconds, accpting clients for game session.
        """
        self.udp_socket.bind(('', SERVER_PORT))
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.tcp_socket.bind((SERVER_IP, SERVER_PORT))

        #we allow up to 40 participants in a game session.
        self.tcp_socket.listen(40)

        #stting timeout for socket for last while iteration to exit in accpt_conn_thread.
        self.tcp_socket.settimeout(1)
        broadcast_thread = Thread(target=self.send_broadcast_messages, args=(self.udp_socket,))
        accpt_conn_thread = Thread(target=self.accept_conn, args=(broadcast_thread, self.tcp_socket))

        #start broadcasting and conntecting to clients a broad.
        broadcast_thread.start()
        accpt_conn_thread.start()

        #wait for the apx 10 second for clients to connect.
        broadcast_thread.join()
        accpt_conn_thread.join()
        self.udp_socket.close()
        self.tcp_socket.close()

    def game_play(self):
        """
            main gameplay method, responsible for calling each clients game thread logic. 
        """

        #check that there is at least one player for a game session to start.
        if len(self.connections) < 1:
            print("not enough players to play restarting server")
            self.client_sockets_close()
            return

        #flag in charge of deviding the clients in two teams by switching team number each time a client is handaled.    
        group_flag = 1

        #for each team, assign to a teams group, 1 or 2 and start game thread. 
        for group in self.connections:
            if group_flag == 1:
                self.group1[group] = 0
                group_flag = 2
            else:
                self.group2[group] = 0
                group_flag = 1
            group_game_trd = Thread(target=self.game_play_trd, args=(self.connections[group], group))
            self.game_treads[group] = group_game_trd
            
            #start game for each group as a thread.
            group_game_trd.start()
        
        #wait for all game sessions to end.
        for trd in self.game_treads:
            print("waiting for trd of "+trd)
            self.game_treads[trd].join()
        
        # finish stage:
        
        # calcutions.
        if self.group1:
            g1_total = sum(self.group1.values())
        else:
            g1_total = 0
        
        if self.group2:
            g2_total = sum(self.group2.values())
        else:
            g2_total = 0

        #procces the end game msg.
        msg = "\nGame over!\n"
        msg += "Group 1 typed in " + str(g1_total) + " characters. Group 2 typed in " + str(g2_total) + " characters.\n"
        if g1_total > g2_total:
            msg += self.str_winner(1, self.group1)
        if g1_total < g2_total:
            msg += self.str_winner(2, self.group2)
        else:
            msg+= "Oh Snap! Its A DRAW!!!!\n "

        #send game results to teams! (and close the connections)    
        for group in self.connections:
            self.connections[group]['client_socket'].send(msg.encode())
            self.connections[group]['client_socket'].close()
        #by by!
        print("Game over, sending out offer requests...")

    def str_winner(self, g_num, group):
        """
            method for preproccesing winning msg for specific winning team.
            params: 
                g_num - the number of the winning group, 1 or 2.
                group - the winning group dictionary
        """
        msg = "Group " + str(g_num) + " wins!\n\nCongratulations to the winners:\n==\n"
        for name in group:
            msg += name
        return msg

    def game_play_trd(self, connection_dict: dict, group_name):
        """
            thread used for game logic for each client connected there will be an instance of this thread to handle its game logic.
            params: 
                connection_dict - {
                    "client_socket" : specified client connection.
                    "adress" :  specified client adress.
                }
                group name - team name.
        """

        #formating the game opening msg.
        msg = """Welcome to Keyboard Spamming Battle Royale.\nGroup 1:\n==\n"""
        for name in self.group1:
            msg += name
        msg += """Group 2:\n==\n"""
        for name in self.group2:
            msg += name
        msg += "\nStart pressing keys on your keyboard as fast as you can!!"

        #sending the msg to coressponding client.
        connection_dict['client_socket'].send(msg.encode())
        counter = 0
        play_until = time.time() + 10

        # for 10 seconds, recive pressed keys from client.
        while time.time() <= play_until:
            incoming_character, a, b = select([connection_dict['client_socket']],[],[],0)
            if incoming_character:
                x = connection_dict['client_socket'].recv(2048).decode()
                counter += 1
        
        #add the accumulated key presses to the team counters dictionary.
        if group_name in self.group1:
            self.group1[group_name] += counter
        else:
            self.group2[group_name] += counter

    def client_sockets_close(self):
        """
            method for closing all clients sockets after use.
        """
        for group in self.connections:
            self.connections[group]["client_socket"].close()

    def crash(self):
        """
            method in case of crash to close used sockets.
        """
        self.client_sockets_close()
        self.tcp_socket.close()
        self.udp_socket.close()


print(f'Server started, listening on IP address {SERVER_IP}')
while 1:
    server = Server()
    try:
        server.waiting_for_clients()
    except Exception:
        traceback.print_exc()
        server.crash()
        continue
    try:
        server.game_play()
    except Exception:
        traceback.print_exc()
        server.client_sockets_close()
        continue
