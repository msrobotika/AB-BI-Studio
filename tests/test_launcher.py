import socket
import pytest
import run


def test_requested_port_validation_and_occupied_port(monkeypatch):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        monkeypatch.setenv('AB_BI_PORT',str(port))
        with pytest.raises(OSError):run.choose_port()
    assert run.choose_port()==port
    monkeypatch.setenv('AB_BI_PORT','80')
    with pytest.raises(ValueError):run.choose_port()
    monkeypatch.setenv('AB_BI_PORT','not a port')
    with pytest.raises(ValueError):run.choose_port()
