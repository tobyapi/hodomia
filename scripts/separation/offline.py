"""Network refusal shared by the comparison scripts; only prepare.py may connect."""
import socket


def deny_network():
    def refuse(*_args, **_kwargs):
        raise RuntimeError('分離の比較はオフラインで実行します。ネット接続は禁止です。')
    socket.create_connection = refuse
    socket.socket.connect = refuse
    socket.socket.connect_ex = refuse
