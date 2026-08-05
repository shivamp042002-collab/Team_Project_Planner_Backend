from boards.models import Task
from validators.common import validate_choice
from datetime import datetime, timezone
from boards.models import Board
from exceptions.errors import ConflictError, InvalidStateError, NotFoundError
from repositories.board_repository import BoardRepository
from repositories.task_repository import TaskRepository
from repositories.team_repository import TeamRepository
from validators.common import validate_max_length, validate_required
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NAME_MAX_LENGTH = 64
DESCRIPTION_MAX_LENGTH = 128
TITLE_MAX_LENGTH = 64
TASK_STATUSES = {"OPEN", "IN_PROGRESS", "COMPLETE"}

class BoardService:
    def __init__(self, board_repository: BoardRepository = None, team_repository: TeamRepository = None,
                 task_repository: TaskRepository = None, user_repository=None, out_dir: Path = None):
        self._boards = board_repository or BoardRepository()
        self._teams = team_repository or TeamRepository()
        self._tasks = task_repository or TaskRepository()
        self._user_repository = user_repository
        self._out_dir = out_dir or (PROJECT_ROOT / "out")

    def _users(self):
        if self._user_repository is None:
            from repositories.user_repository import UserRepository
            self._user_repository = UserRepository()
        return self._user_repository

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

    def add_task(self, title: str, description: str, user_id: str, board_id: str) -> dict:
        board = self._get_board_or_raise(board_id)
        if board["status"] != "OPEN":
            raise InvalidStateError("Cannot add a task to a board that is not OPEN")

        validate_required(title, "title")
        validate_required(description, "description")
        validate_required(user_id, "user_id")
        validate_max_length(title, TITLE_MAX_LENGTH, "title")
        validate_max_length(description, DESCRIPTION_MAX_LENGTH, "description")

        if self._users().get_by_id(user_id) is None:
            raise NotFoundError(f"No user found with id '{user_id}'")
        if self._tasks.get_by_title_and_board(title, board_id) is not None:
            raise ConflictError(f"A task with title '{title}' already exists on this board")

        task = Task(
            id=TaskRepository.generate_id(),
            board_id=board_id,
            title=title,
            description=description,
            user_id=user_id,
            status="OPEN",
            creation_time=datetime.now(timezone.utc).isoformat(),
        )
        self._tasks.add(task.to_dict())
        return task.to_dict()

    def update_task_status(self, task_id: str, status: str) -> dict:
        task = self._tasks.get_by_id(task_id)
        if task is None:
            raise NotFoundError(f"No task found with id '{task_id}'")
        validate_choice(status, TASK_STATUSES, "status")
        return self._tasks.update(task_id, {"status": status})

    def export_board(self, board_id: str) -> str:
        board = self._get_board_or_raise(board_id)
        tasks = self._tasks.get_tasks_for_board(board_id)

        self._out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{board_id}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.txt"
        file_path = self._out_dir / filename

        content = self._render_board(board, tasks)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return filename

    def _render_board(self, board: dict, tasks: list) -> str:
        lines = [
            f"BOARD: {board['name']}",
            f"Status: {board['status']}",
            f"Description: {board['description']}",
            f"Created: {board['creation_time']}",
        ]
        if board.get("end_time"):
            lines.append(f"Closed: {board['end_time']}")
        lines.append("=" * 50)

        for status in ("OPEN", "IN_PROGRESS", "COMPLETE"):
            group = [t for t in tasks if t["status"] == status]
            lines.append(f"\n{status} ({len(group)})")
            lines.append("-" * 30)
            if not group:
                lines.append("  (none)")
            for task in group:
                assignee = self._users().get_by_id(task["user_id"])
                assignee_name = assignee["display_name"] if assignee else "Unknown"
                lines.append(f"  [{task['id'][:8]}] {task['title']} — assigned to {assignee_name}")
                lines.append(f"      {task['description']}")

        return "\n".join(lines) + "\n"