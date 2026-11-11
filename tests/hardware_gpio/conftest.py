"""The hardware backend is tested through substitutes, never live GPIO/network."""
import socket
import sys

import pytest


@pytest.fixture(autouse=True)
def no_physical_io(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("hardware_gpio tests must inject all physical transports")

    monkeypatch.setitem(sys.modules, "lgpio", None)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
