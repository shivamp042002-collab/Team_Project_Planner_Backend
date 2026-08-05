from datetime import datetime, timezone

from boards.models import Board
from exceptions.errors import ConflictError, InvalidStateError, NotFoundError
from repositories.board_repository import BoardRepository
from repositories.task_repository import TaskRepository
from repositories.team_repository import TeamRepository
from validators.common import validate_max_length, validate_required

NAME_MAX_LENGTH = 64
DESCRIPTION_MAX_LENGTH = 128


class BoardService:
    def __init__(self, board_repository: BoardRepository = None, team_repository: TeamRepository = None,
                 task_repository: TaskRepository = None):
        self._boards = board_repository or BoardRepository()
        self._teams = team_repository or TeamRepository()
        self._tasks = task_repository or TaskRepository()

    def _get_board_or_raise(self, board_id: str) -> dict:
        board = self._boards.get_by_id(board_id)
        if board is None:
            raise NotFoundError(f"No board found with id '{board_id}'")
        return board

    def create_board(self, name: str, description: str, team_id: str) -> dict:
        validate_required(name, "name")
        validate_required(description, "description")
        validate_required(team_id, "team_id")
        validate_max_length(name, NAME_MAX_LENGTH, "name")
        validate_max_length(description, DESCRIPTION_MAX_LENGTH, "description")

        if self._teams.get_by_id(team_id) is None:
            raise NotFoundError(f"No team found with id '{team_id}'")
        if self._boards.get_by_name_and_team(name, team_id) is not None:
            raise ConflictError(f"A board with name '{name}' already exists for this team")

        board = Board(
            id=BoardRepository.generate_id(),
            name=name,
            description=description,
            team_id=team_id,
            status="OPEN",
            creation_time=datetime.now(timezone.utc).isoformat(),
        )
        self._boards.add(board.to_dict())
        return board.to_dict()

    def close_board(self, board_id: str) -> dict:
        board = self._get_board_or_raise(board_id)
        if board["status"] == "CLOSED":
            raise InvalidStateError(f"Board '{board_id}' is already closed")

        tasks = self._tasks.get_tasks_for_board(board_id)
        incomplete = [t for t in tasks if t["status"] != "COMPLETE"]
        if incomplete:
            raise InvalidStateError("All tasks must be COMPLETE before closing the board")

        return self._boards.update(board_id, {
            "status": "CLOSED",
            "end_time": datetime.now(timezone.utc).isoformat(),
        })

    def list_boards(self, team_id: str) -> list:
        if self._teams.get_by_id(team_id) is None:
            raise NotFoundError(f"No team found with id '{team_id}'")
        boards = self._boards.get_boards_for_team(team_id, status="OPEN")
        return [{"id": b["id"], "name": b["name"]} for b in boards]