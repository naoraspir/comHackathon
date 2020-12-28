import enum
import time
import traceback
from socket import *
from threading import *
import struct

SERVER_PORT = 2080
SERVER_IP = gethostbyname(gethostname())


class Server:
    def __init__(self):
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.tcp_socket = socket(AF_INET, SOCK_STREAM)
        self.connections = {}
        self.game_treads = {}
        self.group1 = {}
        self.group2 = {}

    def send_broadcast_messages(self, udp_socket):
        message_to_send = struct.pack('Ibh', 0xfeedbeef, 0x2, SERVER_PORT)
        send_until = time.time() + 10
        while time.time() <= send_until:
            udp_socket.sendto(message_to_send, ('<broadcast>', 13117))
            time.sleep(1)

    def accept_conn(self, broadcast_thread, tcp_socket):
        while broadcast_thread.is_alive():
            try:
                client_socket, address = tcp_socket.accept()
                group_name = client_socket.recv(2048).decode()
                self.connections[group_name] = {"client_socket": client_socket, "address": address}
            except timeout:
                # traceback.print_exc()
                continue

    def waiting_for_clients(self):
        """
            This function sends UDP broadcast messages each 1 sec
            for 10 seconds and listening for clients responses.
        """
        self.udp_socket.bind(('', SERVER_PORT))
        self.udp_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.tcp_socket.bind(('', SERVER_PORT))
        self.tcp_socket.listen(20)
        self.tcp_socket.settimeout(2)
        broadcast_thread = Thread(target=self.send_broadcast_messages, args=(self.udp_socket,))
        accpt_conn_thread = Thread(target=self.accept_conn, args=(broadcast_thread, self.tcp_socket))
        broadcast_thread.start()
        accpt_conn_thread.start()
        broadcast_thread.join()
        accpt_conn_thread.join()
        self.udp_socket.close()
        self.tcp_socket.close()

    def game_play(self):
        if len(self.connections) < 1:  # TODO check how many is the lower bound to start a game.
            print("not enough players to play restarting server")
            self.client_sockets_close()
            return
        group_flag = 1
        self.group2['group'] = 5
        for group in self.connections:
            if group_flag == 1:
                self.group1[group] = 0
                group_flag = 2
            else:
                self.group2[group] = 0
                group_flag = 1
            group_game_trd = Thread(target=self.game_play_trd, args=(self.connections[group], group))
            self.game_treads[group] = group_game_trd
            group_game_trd.start()
        for trd in self.game_treads:
            print("waiting for trd of "+trd)
            self.game_treads[trd].join()
        # finish!!
        g1_total = sum(self.group1.values())
        g2_total = sum(self.group2.values())
        msg = "\nGame over!\n"
        msg += "Group 1 typed in " + str(g1_total) + " characters. Group 2 typed in " + str(g2_total) + " characters.\n"
        if g1_total >= g2_total:
            msg += self.str_winner(1, self.group1)
        else:
            msg += self.str_winner(2, self.group2)
        for group in self.connections:
            self.connections[group]['client_socket'].send(msg.encode())
            self.connections[group]['client_socket'].close()
        print("Game over, sending out offer requests...")

    def str_winner(self, g_num, group):
        msg = "Group " + str(g_num) + " wins!\n\nCongratulations to the winners:\n==\n"
        for name in group:
            msg += name
        return msg

    def game_play_trd(self, connection_dict: dict, group_name):
        msg = """Welcome to Keyboard Spamming Battle Royale.\nGroup 1:\n==\n"""
        for name in self.group1:
            msg += name
        msg += """Group 2:\n==\n"""
        for name in self.group2:
            msg += name
        msg += "\nStart pressing keys on your keyboard as fast as you can!!"
        connection_dict['client_socket'].send(msg.encode())
        counter = 0
        play_until = time.time() + 10
        while time.time() <= play_until:
            x = connection_dict['client_socket'].recv(2048).decode()
            print(x)
            counter += 1
            # time.sleep(0)
        print('finished BBC')
        if group_name in self.group1:
            self.group1[group_name] += counter
        else:
            self.group2[group_name] += counter

    def client_sockets_close(self):
        for group in self.connections:
            self.connections[group]["client_socket"].close()

    def crash(self):
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
