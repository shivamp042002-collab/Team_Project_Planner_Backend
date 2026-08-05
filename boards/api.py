import json

from project_board_base import ProjectBoardBase
from services.board_service import BoardService


class BoardApi(ProjectBoardBase):
    def __init__(self, board_service: BoardService = None):
        self._service = board_service or BoardService()

    def create_board(self, request: str):
        data = json.loads(request)
        board = self._service.create_board(
            name=data.get("name"),
            description=data.get("description"),
            team_id=data.get("team_id"),
        )
        return json.dumps({"id": board["id"]})

    def close_board(self, request: str) -> str:
        data = json.loads(request)
        self._service.close_board(board_id=data.get("id"))
        return json.dumps({})

    def list_boards(self, request: str) -> str:
        data = json.loads(request)
        boards = self._service.list_boards(team_id=data.get("id"))
        return json.dumps(boards)

    def add_task(self, request: str) -> str:
        raise NotImplementedError("add_task will be implemented in Milestone 5")

    def update_task_status(self, request: str):
        raise NotImplementedError("update_task_status will be implemented in Milestone 5")

    def export_board(self, request: str) -> str:
        raise NotImplementedError("export_board will be implemented in Milestone 6")