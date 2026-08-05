from typing import Optional

from repositories.base_repository import BaseRepository


class TaskRepository(BaseRepository):
    def __init__(self, db_dir=None):
        super().__init__("tasks", db_dir=db_dir)

    def get_by_title_and_board(self, title: str, board_id: str) -> Optional[dict]:
        matches = self.find(title=title, board_id=board_id)
        return matches[0] if matches else None

    def get_tasks_for_board(self, board_id: str) -> list:
        return self.find(board_id=board_id)