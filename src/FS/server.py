import json
import os
import socket
from platform import system
from alive_progress import alive_bar


def gfs():
    return "\\" if system() == "Windows" else "/"


def normalize_path(p):
    if system() == "Windows":
        OO = "/"
        NN = gfs()
    else:
        OO = "\\"
        NN = gfs()
    p = p.replace(OO, NN)
    p = p.split(NN)
    for e in range(len(p)):
        if e == 0:
            pass
        elif p[e] == "":
            p.pop(e)
    p = NN.join(p)
    return p


class server:
    """server object adjusted to easily interact with the UI"""

    clients = []

    def __init__(self,
                 host: str = "0.0.0.0",
                 port: int = 22000,
                 max_connections: int = 5,
                 buffer_size: int = 0):

        assert isinstance(host, str), exit('HOST attribute must be type STRING')
        assert isinstance(port, int), exit('PORT attribute must be type INT')
        assert isinstance(max_connections, int), exit('max_connections attribute must be type INT')
        assert isinstance(buffer_size, int), exit('buffer_size attribute must be type INT')
        assert buffer_size % 2 == 0, exit('buffer_size attribute must be a integer with module 2 of ZERO')

        self.HOST = host
        self.port = port
        self.max_connections = max_connections
        self.client_sock = None
        self.address = None
        self.buffer_size = 128000 if buffer_size == 0 else buffer_size

        self.sock = socket.create_server(address=(self.HOST, self.port), family=socket.AF_INET)

    def manage(self):
        """Must manage the connections, and loops of cycle."""

        # Main loop for incoming connections.
        return self.serve()

    def serve(self):
        """start serving: accept the connections, then store and returns them."""

        try:
            client_sock, address = self.sock.accept()
            self.client_sock = client_sock
            self.address = address
            client_object = client_side(self, client_sock, address)
            self.clients.append({"object": client_object})
            return client_object
        except OSError:
            exit("error under TCP serving")
            return None

    def close(self):
        self.sock.close()
        self.sock = None


class client_side:

    def __init__(self, server_instance, client_sock, address):

        self.server = server_instance
        self.sock = client_sock
        self.address = address
        self.connected = False
        self.internal_separator = b":"*5
        self.external_separator = b":"*2 + b"$"*2 + b":"*2 + b"$"*2 + b":"*2
        self.size_separator = b":"*2 + b"<>" + b":"*2
        self.dict_separator = b":"*2 + b"><" + b":"*2
        self.EOF = b'["END_OF_' + b'FILE"]'
        self.EOB = b'["ENDOF_BYTES"]'
        self.files = []

    def organize_data_dir(self, reception):
        """pre-organize the data when is sent from a directory, therefore it needs to be organized in the main method"""
        if self.external_separator in reception and reception[-15:] == self.EOF:
            reception = reception.split(self.external_separator)

            files = []
            for e in reception:
                files.append(e)

            return files

    def organize_data(self, reception) -> list and bool:
        """organize and store the bytes received."""

        def order(disordered_bytes):
            """separate the data in (bytes, file name)"""

            disordered_bytes = disordered_bytes.split(self.internal_separator)
            _file_bytes = disordered_bytes[0]
            _file_data = disordered_bytes[1][0:-15] if self.EOF in disordered_bytes[1] else disordered_bytes[1]
            return _file_bytes, _file_data

        assert self.EOB and reception[-15:] == self.EOB in reception, \
            exit("RECEPTION has not the format required. END OF BYTES REQUIRED.")

        result, reception, is_dir = [], reception[0:-15], True if self.external_separator in reception else False

        if is_dir:
            reception = reception.split(self.external_separator)
            for e in reception:
                result.append(order(e))
        elif not is_dir:
            result.append(order(reception))

        return result

    def close(self):
        """Closes the connection of this socket."""
        self.sock.close()
        self.connected = False

    def receive(self):
        """starts a loop receiving bytes until EOF is reached."""

        print("WAITING ")
        receptor = self.sock.recv(48)

        receptor = receptor.split(self.size_separator)
        size, receptor = int(receptor[0]), self.size_separator.join(receptor[1:])

        units = {"B": 1, "KB": 1000, "MB": 1_000_000, "GB": 1_000_000_000}
        unit = "B" if size < 1000 else "KB" if size < 1_000_000 else "MB" if size < 1_000_000_000 else "GB"
        total = int(size / units[unit])

        with alive_bar(total=total, title=f"DOWNLOADING {total}{unit}") as bar:
            addition = len(receptor)
            while True:

                reception = self.sock.recv(self.server.buffer_size)
                receptor += reception

                addition += len(reception)
                if addition > units[unit]:
                    for _ in range(addition // units[unit]):
                        addition -= units[unit]
                        bar(1)

                if receptor[len(receptor) - 15:] == self.EOB:
                    # FILE COMPLETELY RECEIVED.
                    break

            return receptor

    def send(self): """Maybe a response when EOF or IDK | delete it? """

    @classmethod
    def create_file(cls, byte, path: str = None):

        def exists_check():
            try:
                if os.path.exists(normalize_path(path)):
                    with open(normalize_path(path), 'rb') as new_file:
                        fi = new_file.read()
                        assert len(fi) == 0, exit('FILE ALREADY EXISTS AND CONTAIN DATA, PROCEED WILL OVERWRITE IT')
                        return False
                else:
                    return False
            except FileNotFoundError:
                return True

        def write():
            try:
                with open(normalize_path(path), 'wb') as new_file:
                    new_file.write(byte)
            except FileNotFoundError as err:
                exit(f"program: Error while creating: {err}")

        try:
            if not exists_check():
                write()
                return True
            return False
        except Exception as exc:
            return False, exc

    def order(self, reception):
        """returns the data dictionary ordered to create the folders and the received bytes from the files."""

        reception = reception.split(self.dict_separator)
        return json.loads(reception[0].decode()), self.dict_separator.join(reception[1:])
