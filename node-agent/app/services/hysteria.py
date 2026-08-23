# In-memory cache of {password: client_id}, pushed here by the backend
# whenever a subscription is created/removed. Same lifetime as the Xray
# gRPC-provisioned clients in app/services/xray.py — lost on container
# restart, which is an accepted tradeoff already established there rather
# than a new one introduced for Hysteria2.
_users: dict[str, str] = {}


def add_user(password: str, client_id: str) -> None:
    _users[password] = client_id


def remove_user(client_id: str) -> None:
    for password, existing_id in list(_users.items()):
        if existing_id == client_id:
            del _users[password]


def authenticate(password: str) -> str | None:
    return _users.get(password)
