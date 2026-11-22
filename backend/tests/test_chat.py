import json

import httpx
import pytest
from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect


def ws(server, room, name):
    return connect(f"ws://{server}/ws/{room}?username={name}", open_timeout=5)


def recv(sock, kind, timeout=3):
    while True:
        msg = json.loads(sock.recv(timeout=timeout))
        if msg["type"] == kind:
            return msg


def send(sock, **payload):
    sock.send(json.dumps(payload))


def test_health_and_default_rooms(server):
    assert httpx.get(f"http://{server}/api/health").json() == {"status": "ok"}
    names = [r["name"] for r in httpx.get(f"http://{server}/api/rooms").json()]
    assert names[:3] == ["general", "random", "dev-talk"]


def test_message_reaches_everyone_in_room(server):
    with ws(server, "general", "alice") as alice:
        assert recv(alice, "history")["messages"] == []
        with ws(server, "general", "bob") as bob:
            recv(bob, "history")
            while (users := recv(alice, "presence")["users"]) != ["alice", "bob"]:
                assert users == ["alice"]
            assert recv(alice, "system")["text"] == "bob joined"

            send(alice, type="message", text="hi bob")
            got = recv(bob, "message")
            assert (got["username"], got["text"]) == ("alice", "hi bob")
            assert recv(alice, "message")["text"] == "hi bob"
        assert recv(alice, "system")["text"] == "bob left"


def test_online_counts(server):
    with ws(server, "random", "alice") as alice, ws(server, "random", "bob") as bob:
        recv(alice, "history"), recv(bob, "history")
        rooms = {r["name"]: r["online"] for r in httpx.get(f"http://{server}/api/rooms").json()}
        assert rooms["random"] == 2 and rooms["general"] == 0


def test_rooms_are_isolated(server):
    with ws(server, "general", "alice") as alice, ws(server, "random", "bob") as bob:
        recv(alice, "history"), recv(bob, "history")
        send(bob, type="message", text="only in random")
        recv(bob, "message")
        with pytest.raises(TimeoutError):
            recv(alice, "message", timeout=0.5)
    assert httpx.get(f"http://{server}/api/rooms/general/messages").json() == []
    assert len(httpx.get(f"http://{server}/api/rooms/random/messages").json()) == 1


def test_history_is_sent_to_new_joiners(server):
    with ws(server, "dev-talk", "alice") as alice:
        recv(alice, "history")
        send(alice, type="message", text="first")
        recv(alice, "message")
    with ws(server, "dev-talk", "carol") as carol:
        assert [m["text"] for m in recv(carol, "history")["messages"]] == ["first"]


def test_typing_goes_to_others_only(server):
    with ws(server, "general", "alice") as alice, ws(server, "general", "bob") as bob:
        recv(alice, "history"), recv(bob, "history")
        send(alice, type="typing", is_typing=True)
        assert recv(bob, "typing") == {"type": "typing", "username": "alice", "is_typing": True}
        with pytest.raises(TimeoutError):
            recv(alice, "typing", timeout=0.5)


def test_duplicate_name_is_rejected(server):
    with ws(server, "general", "alice") as alice:
        recv(alice, "history")
        with ws(server, "general", "ALICE") as dup:
            with pytest.raises(ConnectionClosed) as exc:
                dup.recv(timeout=3)
            assert exc.value.rcvd.code == 4409


@pytest.mark.parametrize("room,name", [("general", ""), ("Bad_Room", "x"), ("general", "%3Cscript%3E")])
def test_bad_input_is_rejected(server, room, name):
    with ws(server, room, name) as sock:
        with pytest.raises(ConnectionClosed) as exc:
            sock.recv(timeout=3)
        assert exc.value.rcvd.code == 4400


def test_long_messages_are_trimmed_and_blank_ignored(server):
    with ws(server, "general", "alice") as alice:
        recv(alice, "history")
        send(alice, type="message", text="   ")
        send(alice, type="message", text="x" * 5000)
        assert len(recv(alice, "message")["text"]) == 1000


def test_rate_limit(server):
    with ws(server, "general", "spammy") as sock:
        recv(sock, "history")
        for i in range(8):
            send(sock, type="message", text=str(i))
        assert recv(sock, "error")["text"] == "Slow down a little."
