#!/usr/bin/env python3
import sys
import socket
import struct
import threading
from openrgb import utils
from typing import Callable
from time import sleep
from enum import Enum

if sys.platform.startswith("linux"):
    NOSIGNAL = socket.MSG_NOSIGNAL
elif sys.platform.startswith("win"):
    NOSIGNAL = 0


class Status(Enum):
    WAITING = 1
    IDLE = 2


class NetworkClient(object):
    '''
    A class for interfacing with the OpenRGB SDK
    '''

    def __init__(self, update_callback: Callable, address: str = "127.0.0.1", port: int = 6742, name: str = "openrgb-python"):
        '''
        :param update_callback: the function to call when data is received
        :param address: the ip address of the SDK server
        :param port: the port of the SDK server
        :param name: the string that will be displayed on the OpenRGB SDK tab's list of clients
        '''
        self.lock = threading.Lock()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((address, port))

        self.listener = threading.Thread(target=self.listen)
        self.listener.daemon = True
        self.listener.start()

        self.callback = update_callback
        self.state = Status.IDLE

        # Sending the client name
        name = bytes(f"{name}\0", 'utf-8')
        self.send_header(0, utils.PacketType.NET_PACKET_ID_SET_CLIENT_NAME, len(name))
        self.send_data(name)

        # Requesting the number of devices
        self.send_header(0, utils.PacketType.NET_PACKET_ID_REQUEST_CONTROLLER_COUNT, 0)
        self.state = Status.WAITING

    def listen(self):
        '''
        Listens for responses from the SDK from a separate thread

        :raises ConnectionError: when it loses connection to the SDK
        '''
        while True:
            header = bytearray(utils.HEADER_SIZE)
            self.sock.recv_into(header)

            # Unpacking the contents of the raw header struct into a list
            buff = list(struct.unpack('ccccIII', header))
            # print(buff[:4])
            if buff[:4] == [b'O', b'R', b'G', b'B']:
                device_id, packet_type, packet_size = buff[4:]
                # print(device_id, packet_type, packet_size)
                if packet_type == utils.PacketType.NET_PACKET_ID_REQUEST_CONTROLLER_COUNT:
                    buff = struct.unpack("I", self.sock.recv(packet_size))
                    self.callback(device_id, packet_type, buff[0])
                    self.state = Status.IDLE
                elif packet_type == utils.PacketType.NET_PACKET_ID_REQUEST_CONTROLLER_DATA:
                    data = bytearray(packet_size)
                    self.sock.recv_into(data)
                    self.callback(device_id, packet_type, utils.ControllerData.unpack(data))
                    self.state = Status.IDLE
            sleep(.05)

    def requestDeviceData(self, device: int):
        '''
        Sends the request for a device's data

        :param device: the id of the device to request data for
        '''
        self.send_header(device, utils.PacketType.NET_PACKET_ID_REQUEST_CONTROLLER_DATA, 0)
        self.state = Status.WAITING
        p = threading.Thread(target=self.timeout)
        p.start()
        p.join(3)
        if p.is_alive():
            raise TimeoutError("OpenRGB SDK Timed out responding to request for device data")

    def send_header(self, device_id: int, packet_type: int, packet_size: int):
        '''
        Sends a header to the SDK

        :param device_id: the id of the device to send a header for
        :param packet_type: a utils.PacketType
        :param packet_size: the full size of the data to be send after the header
        '''
        if packet_size > 0:
            self.lock.acquire()
        self.sock.send(struct.pack('ccccIII', b'O', b'R', b'G', b'B', device_id, packet_type, packet_size), NOSIGNAL)

    def send_data(self, data: bytes):
        self.sock.send(data, NOSIGNAL)
        self.lock.release()

    def timeout(self):
        while self.state == Status.WAITING:
            sleep(.05)
