import json
import pickle
import socket
import threading
from typing import Any


class ClientSocket:
    def __init__(self, host: str = '127.0.0.1', port: int = 12345, buflen: int = 4096,
                 client_socket: socket.socket = None):
        self.host = host
        self.port = port
        self.buflen = buflen
        self.client_socket = client_socket

    def _buflen(self, buflen: int):
        if buflen < 0:
            return self.buflen
        else:
            return buflen

    def connect(self) -> None:
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return self.client_socket.connect((self.host, self.port))

    def send(self, data: bytes) -> int:
        return self.client_socket.send(data)

    def recv(self, buflen: int = -1) -> bytes:
        return self.client_socket.recv(self._buflen(buflen))

    def recv_all(self, buflen: int = -1) -> bytes:
        data = b""
        while True:
            trunk_data = self.client_socket.recv(self._buflen(buflen))
            if not trunk_data:
                return data
            data += trunk_data

    def send_str(self, string: str, encoding: str = 'utf-8') -> int:
        return self.client_socket.send(string.encode(encoding))

    def recv_str(self, encoding: str = 'utf-8', buflen: int = -1) -> str:
        return self.client_socket.recv(self._buflen(buflen)).decode(encoding)

    def send_json(self, json_data: object, encoding: str = 'utf-8') -> int:
        return self.send_str(json.dumps(json_data), encoding)

    def recv_json(self, encoding: str = 'utf-8', buflen: int = -1) -> object:
        return json.loads(self.recv_str(encoding, buflen))

    def send_obj(self, obj: object) -> int:
        return self.client_socket.send(pickle.dumps(obj))

    def recv_obj(self, buflen: int = -1) -> object:
        return pickle.loads(self.client_socket.recv(self._buflen(buflen)))

    def close(self) -> None:
        return self.client_socket.close()

    def receive_file(self, output_path: str, buflen: int = -1) -> str:
        with open(output_path, 'wb') as f:
            while True:
                data = self.recv(self._buflen(buflen))
                if not data:
                    break
                f.write(data)
        return output_path

    def send_file(self, input_path: str, buflen: int = -1) -> str:
        with open(input_path, 'rb') as f:
            while True:
                data = f.read(self._buflen(buflen))
                if not data:
                    break
                self.client_socket.send(data)
        return input_path


class ServerSocket:
    def __init__(self, host: str = '127.0.0.1', port: int = 12345, backlog: int = 1):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(backlog)

    def accept(self) -> tuple[ClientSocket, Any]:
        client_socket, addr = self.server_socket.accept()
        return ClientSocket(client_socket=client_socket), addr

    @staticmethod
    def client_handler(client_socket, func, args=None, kwargs=None):
        if not args:
            args = []
        client_handler = threading.Thread(target=func, args=(client_socket, *list(args)), kwargs=kwargs)
        client_handler.start()
