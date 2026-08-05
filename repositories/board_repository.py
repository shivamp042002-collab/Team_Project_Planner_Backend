from typing import Optional

from repositories.base_repository import BaseRepository


class BoardRepository(BaseRepository):
    def __init__(self, db_dir=None):
        super().__init__("boards", db_dir=db_dir)

    def get_by_name_and_team(self, name: str, team_id: str) -> Optional[dict]:
        matches = self.find(name=name, team_id=team_id)
        return matches[0] if matches else None

    def get_boards_for_team(self, team_id: str, status: str = None) -> list:
        boards = self.find(team_id=team_id)
        if status is not None:
            boards = [b for b in boards if b["status"] == status]
        return boards