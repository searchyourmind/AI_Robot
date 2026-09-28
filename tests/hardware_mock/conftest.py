"""Offline suite guard: accidental real network connection is a test failure."""
import socket

import pytest


@pytest.fixture(autouse=True)
def no_real_network(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("hardware_mock tests must inject HTTP/model transports")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
