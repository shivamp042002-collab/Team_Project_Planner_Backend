from dataclasses import dataclass, asdict, field
@dataclass
class Team:
    id: str
    name: str
    description: str
    admin: str
    creation_time: str
    member_ids: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)