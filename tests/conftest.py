import socket

import pytest


@pytest.fixture
def next_available_local_port():
    sock = socket.socket()
    sock.bind(("", 0))
    return sock.getsockname()[1]
