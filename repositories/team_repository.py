from typing import Optional
from repositories.base_repository import BaseRepository

class TeamRepository(BaseRepository):
    def __init__(self, db_dir=None):
        super().__init__("teams", db_dir=db_dir)

    def get_by_name(self, name: str) -> Optional[dict]:
        matches = self.find(name=name)
        return matches[0] if matches else None

    def get_teams_for_user(self, user_id: str) -> list:
        return [t for t in self.get_all() if user_id in t.get("member_ids", [])]