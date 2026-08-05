from dataclasses import dataclass, asdict

@dataclass
class User:
    id: str
    name: str
    display_name: str
    creation_time: str

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "User":
        return User(
            id=data["id"],
            name=data["name"],
            display_name=data["display_name"],
            creation_time=data["creation_time"],
        )