import argparse
from functools import partial
from server import *
from client import *


def gfs():
    return "\\" if system() == "Windows" else "/"


def gfsv(v):
    if isinstance(v, bytes):
        return b"\\" if b"\\" in v else b"/"
    if isinstance(v, str):
        return "\\" if "\\" in v else "/"


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


def get_default_folder():
    return normalize_path(f"{os.getcwd()}\\server_files")


def get_folder():
    """Returns the configured folder path to store the files."""

    # create config file if it does not exist and specify the default folder.
    if not os.path.exists("config.json"):
        with open("config.json", "w") as file:
            file.write(json.dumps({"storage_folder": get_default_folder()}))

    with open("config.json", "r") as file:
        try:
            folder_path = file.read()

            if folder_path == "":
                exit("program: Unknown error: MAIN.PY > config.json BAD CONFIGURED (it is empty.)")
                raise ValueError
            else:
                folder_path = json.loads(folder_path)

            if type(folder_path) is not dict and "storage_folder" in folder_path.keys():
                exit("program: Unknown error: MAIN.PY > config.json BAD CONFIGURED (keys err).")

            data = folder_path["storage_folder"]

            try:
                if not os.path.exists(data):
                    os.mkdir(data)
            except OSError as nw:
                exit(nw)

            return data
        except KeyError:
            print("config.json seems to be corrupted, now is fixed with the default folder.")
            set_folder()
            return get_default_folder()


def set_folder(param: str = get_default_folder()):
    if not os.path.isdir(param):
        try:
            # split the folder path to create its route and/or it if it does not exist.
            param_l = normalize_path(param).split(gfs())
            for i, e in enumerate(param_l):
                if i == 0:
                    continue
                try:
                    os.mkdir(gfs().join(param_l[0:i + 1]))
                except OSError:
                    pass

            # this should throw the error if was not possible to create the folder.
            if not os.path.exists(param):
                print("should be created ", param)
                os.mkdir(param)

        except OSError as err:
            exit(f"The specified folder |--dir {param} | "
                 f"does not exist and an error happens while trying to create it: {err}\n"
                 "Specify a valid folder.")

    if os.path.exists(param):
        with open("config.json", "w") as file:
            file.write(json.dumps({"storage_folder": param}))


def scan_mode(value):
    try:
        if value.lower() in ["server", "sv", "client", "cli"]:
            return value
        exit(f"program: The chosen mode is not in the options: server | sv | client | cli ")
        return False
    except ValueError:
        exit(f"program: The chosen mode is not in the options: server | sv | client | cli ")
        return False


def scan_host(value):
    def define(v, display):
        try:
            int(v)
        except ValueError:
            exit(f"program: {display}")

    value.replace(" ", "")
    if ":" in value:
        # HOST:PORT
        if not len(value.split(":")) == 2:
            exit("program: The HOST:PORT combination is wrong. It must had only a host and a port.")
        for i, integer in enumerate(value.split(":")):
            # remove periods if scanning host.
            define("".join(integer.split(".")) if i == 0 else integer,
                   f"Error in {'host' if i == 0 else 'port'}.\n"
                   "The HOST:PORT combination must be constituted only by NUMBERS. "
                   "e.g 192.168.1.22:1522")
    else:
        define(value,
               f"Error in port.\n"
               "The PORT must be constituted only by NUMBERS. "
               "e.g 1522")
    return value


space = "\u00A0" * 2222
parser = argparse.ArgumentParser(
    description="starts a server or client process to respectively receive or "
                "send files over the local network.",
    epilog=f"""examples:   {space}                 
                                         \u00A0python -m send server 2200   {space}                                                         
                                         \u00A0python -m send client 192.168.1.100:2200 """)

parser.add_argument('mode', action="store", metavar="mode", default="server", type=scan_mode,
                    help="Specify the port to open the local server.\n"
                         "(default: server)")

parser.add_argument('host', action="store", metavar="host:port", default=22000, type=scan_host,
                    help=f"The local port to serve on, or host:port combination of the server to connect to. \n"
                         "(default: 22000)")

parser.add_argument('-d', '--dir', action="store", metavar="", default=get_folder(),
                    help=f"The path to the directory where you want to store the received files.\n"
                         f"default: {get_folder()}  -  do '-d . ' to reset folder. ")

args = parser.parse_args()


class process:
    new_dir = args.dir != "." and args.dir != get_folder()
    def_dir = args.dir == "." and get_folder() != get_default_folder()
    if new_dir or def_dir:
        last = get_folder()
        actual = args.dir if args.dir != "." else get_default_folder()
        set_folder(actual)
        print(f"Default directory successfully changed."
              f"\n directory is now: | {actual} | ")

    def __init__(self, mode: str, host: str | int):
        self.dir = get_folder()
        self.server = ...
        self.client = ...
        self.port = ...

        assert mode is not None, exit(f"program: You must specify a mode.")
        assert host is not None, exit(f"program: You must specify a host.")

        self.mode = mode
        self.host = host

        getattr(self, f"init_{mode}")()

    def init_server(self):
        self.host = int(self.host)
        if not os.path.isdir(self.dir) and os.path.exists(self.dir):
            if not os.path.exists(self.dir):
                exit("program: DIRECTORY DOES NOT EXIST.")
        setattr(self, "dir", self.dir)
        self.start_server()

    def init_client(self):
        split_host = self.host.split(":")
        setattr(self, "port", split_host[1])
        self.host = split_host[0]
        self.start_client()

    def start_server(self):
        setattr(self, "server", server(port=int(self.host)))
        print(f"\nSERVING ON |0.0.0.0:{args.host}| ")
        self.input_loop(partial(self.exe_connection), "listen a new connection")

    def start_client(self):
        setattr(self, "client", client(self.host, int(self.port)))
        if self.client.connect():
            print(f"\nCONNECTED TO {self.host}:{self.port} AS CLIENT")
            self.input_loop(partial(self.exe_sending), "send a new file or directory")
            exit("program: Exit.")
        else:
            exit("program: Error trying to connect, please restart the program.")

    def exe_connection(self):
        print(f"\nListening for incoming connection.")
        setattr(self, "client", self.server.manage())
        if self.client is not None:
            addr = self.client.address
            print(f"INCOMING CONNECTION FROM {addr[0]}:{addr[1]}")
            self.input_loop(partial(self.exe_files), "listen a new file or directory")
            self.client.close()

    def exe_files(self):
        print("\nListening for incoming files.")
        listener = self.client.receive()

        data_dict, listener = self.client.order(listener)

        if len(listener) > 15 and b'["ENDOF_BYTES"]' == listener[-15:]:
            pos_b = 0
            pos_n = 1

            size = len(listener)
            units = {"B": 1, "KB": 1000, "MB": 1_000_000, "GB": 1_000_000_000}
            unit = "B" if size < 1000 else "KB" if size < 1_000_000 else "MB" if size < 1_000_000_000 else "GB"

            integer = int(size / units[unit])
            decimal = '' if unit == 'B' else str((size / units[unit]) % 1)[1:4]
            display_formatted = f'{integer}{decimal}{unit}'
            print("DATA RECEIVED: ", display_formatted)

            # iteration of file(TUPLE) in the received data.
            result = self.client.organize_data(listener)

            is_dir = type(data_dict) == dict

            if is_dir:
                # normalize keys(folder and sub folders path) to the current system.
                new_dd = {}
                for key in iter(data_dict):
                    new_key = normalize_path(key)
                    new_dd[new_key] = data_dict[key]

                    try:
                        os.mkdir(gfs().join([self.dir, new_key]))
                    except OSError:
                        pass

                data_dict = new_dd

            for file in result:

                name = normalize_path(file[pos_n].decode()).encode()
                name_list = name.split(gfsv(name))
                full_path = gfs().encode().join([self.dir.encode(), name])
                current = name_list[-1].decode()
                is_directory, is_file = False, False

                if type(data_dict) == dict:
                    is_directory = current in data_dict[gfsv(name).join(name_list[0:-1]).decode()]
                elif type(data_dict) == str:
                    is_file = current == data_dict

                if is_directory or is_file:
                    if self.client.create_file(file[pos_b], full_path.decode()):
                        ...
                    else:
                        exit("Error while creating! ")
                else:
                    exit("ERROR BEFORE CREATING.")

    def exe_sending(self):
        print("Insert the path of the file or directory you want to send.")
        path = input(" >")
        path = normalize_path(path)

        if os.path.isfile(path) or os.path.isdir(path) and os.path.exists(path):
            self.client.send(path)
            print(f"Correctly sent {'DIRECTORY' if os.path.isdir(path) else 'FILE'}: {path}.")
        else:
            print("An error occurs trying to send the file... Please be sure it is correct and exists.")

    @classmethod
    def input_loop(cls, execute, listen):
        decision = ""
        while decision.lower() == "":
            execute()
            decision = input(f"\nDo you want to {listen.lower()} ?   Enter to continue  |  any key+enter to stop.")
            decision.replace(" ", "")


if __name__ == "__main__":
    pr = process(args.mode, args.host)

# DO THE PROGRESS BAR TO THE CLIENT
