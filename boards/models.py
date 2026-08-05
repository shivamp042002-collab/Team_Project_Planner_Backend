from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Board:
    id: str
    name: str
    description: str
    team_id: str
    status: str
    creation_time: str
    end_time: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Task:
    id: str
    board_id: str
    title: str
    description: str
    user_id: str
    status: str
    creation_time: str

    def to_dict(self) -> dict:
        return asdict(self)