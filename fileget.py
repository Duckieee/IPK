#!/usr/bin/env python3
# VUT FIT: Počítačové komunikace a sítě
# Projekt 1: Triviální distribuovaný souborový systém
# Kateřina Cibulcová (xcibul12)
# Letní semestr 2020/2021

import socket
import argparse
import sys
import os
import re


# ---------- Funkce pro stahovani souboru ----------- #

def get_request(fileserver_ip, fileserver_port, fn):
    try:
        data_chunks = []
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(30)
        try:
            s.connect((fileserver_ip, fileserver_port))
        except TimeoutError:
            print('Server Time Out - Connection Failed.')
            sys.exit(1)

        request = 'GET {fn} FSP/1.0\r\nAgent: xcibul12\r\nHostname:{fs}\r\n\r\n'.format(fn=fn, fs=fileserver)
        request = request.encode()

        s.send(request)

        while 1:
            data = s.recv(4096)
            if not data:
                break

            data_chunks.append(data)

        reply = b''.join(data_chunks)
        parts = reply.split(b'\r\n\r\n', 1)
        file_header = parts[0]
        file_content = parts[1]

        if file_header.split(b'\r\n')[0] != b'FSP/1.0 Success':
            print('Error!', str(file_content, 'utf-8'))
            if index_mode:
                return
            else:
                sys.exit(1)

        filename = fn
        dirs = ""
        if '/' in fn:
            filename = fn.rsplit('/', 1)[1]
            dirs = fn.rsplit('/', 1)[0]

        cwd = os.getcwd()
        path = os.path.join(cwd, dirs)
        filename = os.path.join(path, filename)

        if index_mode:
            os.makedirs(path, exist_ok=True)

        if os.path.isfile(filename):
            print("This file already exists. Data will be overwritten.")

        with open(filename, 'wb') as file:
            file.write(file_content)
            file.close()

        return file_content

    except socket.error as e:
        print(e)
        sys.exit()

# ---------- Hlavni funkce programu ----------- #


def main():
    try:
        # ---------- NSP ---------- #
        nsp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        nsp.settimeout(5)
        request = 'WHEREIS {fs}\r\n'.format(fs=fileserver)
        request = request.encode()
        try:
            nsp.sendto(request, (server_ip, int(server_port)))
        except TimeoutError:
            print('Server Time Out')
            sys.exit(1)

        reply = nsp.recv(4096)

        nsp.close()

        reply = str(reply, 'utf-8')

        if reply.split()[0] == 'ERR':
            print('Error!', reply)
            sys.exit(1)

        # ---------- FSP ---------- #

        fileserver_info = reply.split()[1]
        fileserver_ip = fileserver_info.split(':')[0]
        fileserver_port = int(fileserver_info.split(':')[1])

        global filepath
        file_content = get_request(fileserver_ip, fileserver_port, filepath)

        if index_mode:
            file_content = (str(file_content, 'utf-8'))
            file_index = file_content.split()
            for f in file_index:
                filename = f
                get_request(fileserver_ip, fileserver_port, filename)
    except socket.timeout:
        print("Server Timeout - Connection failed.")
        sys.exit()
    except socket.error as e:
        print(e)
        sys.exit()


# ---------- Zpracovani argumentu programu ---------- #

parser = argparse.ArgumentParser(description='IPK projekt: Klient pro distribuovaný souborový systém')

parser.add_argument('-n', nargs=1, metavar='NAMESERVER', help='IP adresa a číslo portu jmenného serveru', required=True,
                    dest='nameserver')
parser.add_argument('-f', nargs=1, metavar='SURL', help='SURL souboru pro stažení. Protokol v URL je vždy fsp.',
                    required=True, dest='surl')
args = parser.parse_args()

# ---------- Zpracovani a kontrola zadanych udaju ---------- #

match = re.search(r'[0-9]+(?:\.[0-9]+){3}(:[0-9]+)?', args.nameserver[0])
if match is None:
    print('Invalid Nameserver Data!')
    sys.exit()

server_ip = args.nameserver[0].split(':')[0]
server_port = args.nameserver[0].split(':')[1]

match = re.search(r'(/.*?\.[\w:]+)', args.surl[0])
if match is None:
    print('Invalid Fileserver Path!')
    sys.exit()

surl = args.surl[0].split('/', 3)
if len(surl) <= 3:
    print('Invalid Fileserver Path!')
    sys.exit()

fileserver = surl[2]

filepath = surl[3]

index_mode = False
if filepath == '*':
    index_mode = True
    filepath = 'index'

main()
