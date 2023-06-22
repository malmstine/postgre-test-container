import socket

OK = "\033[92m"
END = "\033[0m"

CONTAINER_NAME = "secret"


def get_free_port() -> int:
    """
    Starts a socket connection to grab a free port
    """
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(("", 0))
    addr, port = tcp.getsockname()
    tcp.close()
    return port

