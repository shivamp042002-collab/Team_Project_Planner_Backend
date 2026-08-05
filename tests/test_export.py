import json
import shutil
import tempfile
import unittest
from pathlib import Path

from exceptions.errors import NotFoundError
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


class ExportBoardTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = Path(tempfile.mkdtemp())
        self._out_dir = self._tmp_dir / "out"

        self.user_repo = UserRepository(db_dir=self._tmp_dir)
        self.team_repo = TeamRepository(db_dir=self._tmp_dir)
        self.board_repo = BoardRepository(db_dir=self._tmp_dir)
        self.task_repo = TaskRepository(db_dir=self._tmp_dir)

        self.user_api = UserApi(user_service=UserService(user_repository=self.user_repo, team_repository=self.team_repo))
        self.team_api = TeamApi(team_service=TeamService(team_repository=self.team_repo, user_repository=self.user_repo))
        self.board_api = BoardApi(board_service=BoardService(
            board_repository=self.board_repo, team_repository=self.team_repo,
            task_repository=self.task_repo, user_repository=self.user_repo,
            out_dir=self._out_dir,
        ))

    def tearDown(self):
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def _create_team_and_board(self):
        admin_id = json.loads(self.user_api.create_user(json.dumps({"name": "admin", "display_name": "Admin A."})))["id"]
        team_id = json.loads(self.team_api.create_team(
            json.dumps({"name": "engineering", "description": "desc", "admin": admin_id})
        ))["id"]
        board_id = json.loads(self.board_api.create_board(
            json.dumps({"name": "sprint-1", "description": "desc", "team_id": team_id})
        ))["id"]
        return board_id, admin_id

    def test_export_board_creates_file_with_task_content(self):
        board_id, user_id = self._create_team_and_board()
        self.board_api.add_task(
            json.dumps({"title": "task-1", "description": "fix bug", "user_id": user_id, "board_id": board_id})
        )

        response = json.loads(self.board_api.export_board(json.dumps({"id": board_id})))
        out_file = self._out_dir / response["out_file"]

        self.assertTrue(out_file.exists())
        content = out_file.read_text()
        self.assertIn("sprint-1", content)
        self.assertIn("task-1", content)
        self.assertIn("Admin A.", content)

    def test_export_nonexistent_board_raises(self):
        with self.assertRaises(NotFoundError):
            self.board_api.export_board(json.dumps({"id": "nonexistent"}))

    def test_export_board_with_zero_tasks_still_produces_file(self):
        board_id, _ = self._create_team_and_board()

        response = json.loads(self.board_api.export_board(json.dumps({"id": board_id})))
        out_file = self._out_dir / response["out_file"]

        self.assertTrue(out_file.exists())
        self.assertIn("(none)", out_file.read_text())


if __name__ == "__main__":
    unittest.main()