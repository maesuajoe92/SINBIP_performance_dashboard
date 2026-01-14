from dataclasses import dataclass
from typing import Optional
from .config import BOARD_USER, BOARD_PASS, MGMT_USER, MGMT_PASS

@dataclass(frozen=True)
class User:
    username: str
    role: str  # "board" or "management"

USERS = {
    BOARD_USER: {"password": BOARD_PASS, "role": "board"},
    MGMT_USER: {"password": MGMT_PASS, "role": "management"},
}

def authenticate(username: str, password: str) -> Optional[User]:
    record = USERS.get(username)
    if not record:
        return None
    if record["password"] != password:
        return None
    return User(username=username, role=record["role"])
