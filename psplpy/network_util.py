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
















def send(host: str, port: int, data: object = None, file_path: str = None, buffer_size: int = 4096,
         ignore_error: bool = True, debug: bool = False) -> None:
    if data and file_path:
        raise ValueError('data and file_path can only be given one')
    elif not data and not file_path:
        raise ValueError('data or file_path must be given one')
    try:
        # creates socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        if data:
            serialized_data = pickle.dumps(data)
            client_socket.send(serialized_data)
        else:
            # opens file and sends data
            with open(file_path, 'rb') as file:
                while True:
                    data = file.read(buffer_size)
                    if not data:
                        break
                    client_socket.send(data)
        # closes socket
        client_socket.close()
        if debug:
            if data:
                print('data send successfully')
            else:
                print(f"File {file_path} send successfully")
    except Exception as e:
        if ignore_error:
            print(f"A Wrong occurred when sending: {str(e)}")
        else:
            raise e


def receive(host: str, port: int, save_path: str = None, buffer_size: int = 4096, ignore_error: bool = True,
            debug: bool = False) -> object:
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(1)

        if debug:
            print(f"Waiting for connection...")
        client_socket, addr = server_socket.accept()
        if debug:
            print(f"Connection from {addr}")

        if save_path:
            with open(save_path, 'wb') as file:
                while True:
                    data = client_socket.recv(buffer_size)
                    if not data:
                        break
                    file.write(data)
            client_socket.close()
            server_socket.close()
            return save_path
        else:
            # Initializes an empty bytes to store the received data
            received_data = b''
            while True:
                data_chunk = client_socket.recv(buffer_size)
                if not data_chunk:
                    break
                received_data += data_chunk
            deserialized_data = pickle.loads(received_data)
            client_socket.close()
            server_socket.close()
            return deserialized_data
    except Exception as e:
        if ignore_error:
            print(f"A Wrong occurred when receiving: {str(e)}")
        else:
            raise e
