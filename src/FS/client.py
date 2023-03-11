import os
import socket
import json
from platform import system
from alive_progress import alive_bar

gfs = "\\" if system() == "Windows" else "/"


class client:

    def __init__(self, server_host: str, server_port: int = 22000):
        assert isinstance(server_host, str), exit('server_host attribute must be type STRING')
        assert isinstance(server_port, int), exit('server_port attribute must be type INT')

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_host = server_host
        self.server_port = server_port
        self.buffer_size = 256
        self.internal_separator = b":" * 5
        self.external_separator = b":" * 2 + b"$" * 2 + b":" * 2 + b"$" * 2 + b":" * 2
        self.size_separator = b":" * 2 + b"<>" + b":" * 2
        self.dict_separator = b":" * 2 + b"><" + b":" * 2
        self.EOF = b'["END_OF_' + b'FILE"]'
        self.EOB = b'["ENDOF_BYTES"]'

    def close(self):
        self.sock.close()

    def connect(self):
        try:
            self.sock.connect((self.server_host, self.server_port))
            return True
        except ConnectionRefusedError:
            return False

    def send(self, path: str):
        """Organize the data (dir or file), then sends it to the connected server."""

        is_dir = os.path.isdir(path)
        is_file = os.path.isfile(path)

        assert isinstance(path, str), exit('path attribute must be type STRING')
        assert os.path.exists(path), exit('path does not exist.')
        assert is_dir or is_file, exit('path must be a directory or a file.')

        def check_file(_file_path, _location):
            """Checks the file to get the bytes and store it with its pertinent data."""
            with open(_file_path, 'rb') as f:
                file_bytes = f.read()
                temporal_file_store.append(file_bytes + self.internal_separator + _location + self.EOF)

        def get_ordered_data() -> bytes:
            """Returns a file name or an ordered json dict as bytes with folders names as keys"""

            current = path.split(gfs)[-1]
            pos_current = path.count(current)  # possible repeated super-dir name

            if is_dir:
                data = {}
                for dire in os.walk(path):
                    _has_sub = dire[0].count(current) == 1
                    curr = current + current.join(dire[0].split(current)[1 if _has_sub else pos_current:])

                    data[curr] = []
                    for n in dire[2]:
                        data[curr].append(n)
            else:
                # Single file
                data = current
            return json.dumps(data).encode()

        temporal_file_store = []
        bytes_store = b''

        data_dict = get_ordered_data()

        if is_file:
            name = path.split(gfs)[-1]
            check_file(path, _location=name.encode())

        elif is_dir:
            main_folder = path.split(gfs)[-1]

            pos_path = 0  # in walk method
            pos_files = 2  # in walk method
            pos_mf = path.count(main_folder)  # possible repeated super-dir name

            # Iter over main directory and sub
            scanned_dirs = list(os.walk(path))
            for i, Dir in enumerate(scanned_dirs):

                # Iter over files of each directory
                for file_name in Dir[pos_files]:
                    file_path = gfs.join([Dir[pos_path], file_name])

                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        has_sub = file_path.count(main_folder) == 1

                        # New location path format truncated on the main folder
                        location = main_folder.join(
                            file_path.split(main_folder)[-1 if has_sub else pos_mf:])[1:].split(gfs)
                        location.pop(-1)  # removes the file name
                        location.insert(0, main_folder)
                        location = gfs.encode().join([gfs.join(location).encode(), file_name.encode()])

                        check_file(file_path, location)

        bytes_store += self.external_separator.join(temporal_file_store)  # files
        bytes_store = data_dict + self.dict_separator + bytes_store + self.EOB  # data dictionary & EOB
        bytes_store = str(len(bytes_store)).encode() + self.size_separator + bytes_store  # total length

        self.sock.sendto(bytes_store, (self.server_host, self.server_port))
