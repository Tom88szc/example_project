
import socket
from typing import Optional


class TcpTransport:
    def __init__(
        self,
        host: str,
        port: int,
        connect_timeout: float = 5.0,
        read_timeout: float = 10.0,
    ):
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.sock: Optional[socket.socket] = None

    def connect(self) -> None:
        self.sock = socket.create_connection((self.host, self.port), timeout=self.connect_timeout)
        self.sock.settimeout(self.read_timeout)

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            finally:
                self.sock = None
