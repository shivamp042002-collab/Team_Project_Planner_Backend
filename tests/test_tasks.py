import json
import shutil
import tempfile
import unittest
from pathlib import Path

from exceptions.errors import ConflictError, InvalidStateError, NotFoundError, ValidationError
from repositories.board_repository import BoardRepository
from repositories.task_repository import TaskRepository
from repositories.team_repository import TeamRepository
from repositories.user_repository import UserRepository
from services.board_service import BoardService
from services.team_service import TeamService
from services.user_service import UserService
from boards.api import BoardApi
from teams.api import TeamApi
from users.api import UserApi


class TaskApiTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = Path(tempfile.mkdtemp())
        self.user_repo = UserRepository(db_dir=self._tmp_dir)
        self.team_repo = TeamRepository(db_dir=self._tmp_dir)
        self.board_repo = BoardRepository(db_dir=self._tmp_dir)
        self.task_repo = TaskRepository(db_dir=self._tmp_dir)

        self.user_api = UserApi(user_service=UserService(user_repository=self.user_repo, team_repository=self.team_repo))
        self.team_api = TeamApi(team_service=TeamService(team_repository=self.team_repo, user_repository=self.user_repo))
        self.board_api = BoardApi(board_service=BoardService(
            board_repository=self.board_repo, team_repository=self.team_repo,
            task_repository=self.task_repo, user_repository=self.user_repo,
        ))

    def tearDown(self):
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def _create_user(self, name):
        return json.loads(self.user_api.create_user(json.dumps({"name": name, "display_name": name})))["id"]

    def _create_team_and_board(self):
        admin_id = self._create_user("admin_user")
        team_id = json.loads(self.team_api.create_team(
            json.dumps({"name": "engineering", "description": "desc", "admin": admin_id})
        ))["id"]
        board_id = json.loads(self.board_api.create_board(
            json.dumps({"name": "sprint-1", "description": "desc", "team_id": team_id})
        ))["id"]
        return board_id, admin_id

    # add_task 

    def test_add_task_valid_returns_id(self):
        board_id, user_id = self._create_team_and_board()
        response = self.board_api.add_task(
            json.dumps({"title": "task-1", "description": "d", "user_id": user_id, "board_id": board_id})
        )
        self.assertIn("id", json.loads(response))

    def test_add_task_duplicate_title_same_board_raises(self):
        board_id, user_id = self._create_team_and_board()
        self.board_api.add_task(
            json.dumps({"title": "task-1", "description": "d", "user_id": user_id, "board_id": board_id})
        )
        with self.assertRaises(ConflictError):
            self.board_api.add_task(
                json.dumps({"title": "task-1", "description": "d2", "user_id": user_id, "board_id": board_id})
            )

    def test_add_task_to_closed_board_raises(self):
        board_id, user_id = self._create_team_and_board()
        self.board_api.close_board(json.dumps({"id": board_id}))
        with self.assertRaises(InvalidStateError):
            self.board_api.add_task(
                json.dumps({"title": "task-1", "description": "d", "user_id": user_id, "board_id": board_id})
            )

    def test_add_task_invalid_user_raises(self):
        board_id, _ = self._create_team_and_board()
        with self.assertRaises(NotFoundError):
            self.board_api.add_task(
                json.dumps({"title": "task-1", "description": "d", "user_id": "nonexistent", "board_id": board_id})
            )

    def test_add_task_title_too_long_raises(self):
        board_id, user_id = self._create_team_and_board()
        with self.assertRaises(ValidationError):
            self.board_api.add_task(
                json.dumps({"title": "a" * 65, "description": "d", "user_id": user_id, "board_id": board_id})
            )

    # update_task_status 

    def test_update_task_status_valid(self):
        board_id, user_id = self._create_team_and_board()
        task_id = json.loads(self.board_api.add_task(
            json.dumps({"title": "task-1", "description": "d", "user_id": user_id, "board_id": board_id})
        ))["id"]

        self.board_api.update_task_status(json.dumps({"id": task_id, "status": "IN_PROGRESS"}))

        self.assertEqual(self.task_repo.get_by_id(task_id)["status"], "IN_PROGRESS")

    def test_update_task_status_invalid_value_raises(self):
        board_id, user_id = self._create_team_and_board()
        task_id = json.loads(self.board_api.add_task(
            json.dumps({"title": "task-1", "description": "d", "user_id": user_id, "board_id": board_id})
        ))["id"]

        with self.assertRaises(ValidationError):
            self.board_api.update_task_status(json.dumps({"id": task_id, "status": "DONE"}))

    def test_update_task_status_nonexistent_task_raises(self):
        with self.assertRaises(NotFoundError):
            self.board_api.update_task_status(json.dumps({"id": "nonexistent", "status": "OPEN"}))

    # full lifecycle: add tasks, complete them, then close board

    def test_close_board_after_completing_all_tasks_succeeds(self):
        board_id, user_id = self._create_team_and_board()
        task_id = json.loads(self.board_api.add_task(
            json.dumps({"title": "task-1", "description": "d", "user_id": user_id, "board_id": board_id})
        ))["id"]

        self.board_api.update_task_status(json.dumps({"id": task_id, "status": "COMPLETE"}))
        self.board_api.close_board(json.dumps({"id": board_id}))  # should not raise


if __name__ == "__main__":
    unittest.main()