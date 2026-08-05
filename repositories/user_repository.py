"""
Repository for User records, backed by db/users.json.
"""
from typing import Optional

from repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, db_dir=None):
        super().__init__("users", db_dir=db_dir)

    def get_by_name(self, name: str) -> Optional[dict]:
        """Return the user record with the given name, or None."""
        matches = self.find(name=name)
        return matches[0] if matches else None