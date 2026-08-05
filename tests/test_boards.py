import json
import shutil
import tempfile
import unittest
from pathlib import Path
import uuid

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


class BoardApiTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = Path(tempfile.mkdtemp())
        self.user_repo = UserRepository(db_dir=self._tmp_dir)
        self.team_repo = TeamRepository(db_dir=self._tmp_dir)
        self.board_repo = BoardRepository(db_dir=self._tmp_dir)
        self.task_repo = TaskRepository(db_dir=self._tmp_dir)

        self.user_api = UserApi(user_service=UserService(user_repository=self.user_repo, team_repository=self.team_repo))
        self.team_api = TeamApi(team_service=TeamService(team_repository=self.team_repo, user_repository=self.user_repo))
        self.board_api = BoardApi(board_service=BoardService(
            board_repository=self.board_repo, team_repository=self.team_repo, task_repository=self.task_repo,
        ))

    def tearDown(self):
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def _create_team(self, name="engineering"):
        admin_id = json.loads(self.user_api.create_user(json.dumps({"name": f"admin-{uuid.uuid4().hex[:8]}", "display_name": "Admin"})))["id"]
        team_id = json.loads(self.team_api.create_team(
            json.dumps({"name": name, "description": "desc", "admin": admin_id})
        ))["id"]
        return team_id, admin_id

    def _create_board(self, team_id, name="sprint-1"):
        response = self.board_api.create_board(
            json.dumps({"name": name, "description": "desc", "team_id": team_id})
        )
        return json.loads(response)["id"]

    # create_board 

    def test_create_board_valid_returns_id(self):
        team_id, _ = self._create_team()
        board_id = self._create_board(team_id)
        self.assertTrue(len(board_id) > 0)

    def test_create_board_duplicate_name_same_team_raises(self):
        team_id, _ = self._create_team()
        self._create_board(team_id, name="sprint-1")
        with self.assertRaises(ConflictError):
            self._create_board(team_id, name="sprint-1")

    def test_create_board_same_name_different_team_allowed(self):
        team1, _ = self._create_team(name="team-a")
        team2, _ = self._create_team(name="team-b")
        self._create_board(team1, name="sprint-1")
        board_id = self._create_board(team2, name="sprint-1")
        self.assertTrue(len(board_id) > 0)

    def test_create_board_invalid_team_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.board_api.create_board(
                json.dumps({"name": "sprint-1", "description": "desc", "team_id": "nonexistent"})
            )

    def test_create_board_name_too_long_raises(self):
        team_id, _ = self._create_team()
        with self.assertRaises(ValidationError):
            self.board_api.create_board(
                json.dumps({"name": "a" * 65, "description": "desc", "team_id": team_id})
            )

    # close_board 

    def test_close_board_with_zero_tasks_succeeds(self):
        team_id, _ = self._create_team()
        board_id = self._create_board(team_id)

        self.board_api.close_board(json.dumps({"id": board_id}))

        boards = json.loads(self.board_api.list_boards(json.dumps({"id": team_id})))
        self.assertEqual(boards, [])  # closed boards don't show in list_boards (OPEN only)

    def test_close_board_with_incomplete_task_raises(self):
        team_id, admin_id = self._create_team()
        board_id = self._create_board(team_id)
        self.task_repo.add({
            "id": TaskRepository.generate_id(), "board_id": board_id, "title": "t1",
            "description": "d", "user_id": admin_id, "status": "OPEN",
            "creation_time": "2026-01-01T00:00:00+00:00",
        })

        with self.assertRaises(InvalidStateError):
            self.board_api.close_board(json.dumps({"id": board_id}))

    def test_close_board_already_closed_raises(self):
        team_id, _ = self._create_team()
        board_id = self._create_board(team_id)
        self.board_api.close_board(json.dumps({"id": board_id}))

        with self.assertRaises(InvalidStateError):
            self.board_api.close_board(json.dumps({"id": board_id}))

    def test_close_board_not_found_raises(self):
        with self.assertRaises(NotFoundError):
            self.board_api.close_board(json.dumps({"id": "nonexistent"}))

    # list_boards 

    def test_list_boards_returns_only_open(self):
        team_id, _ = self._create_team()
        open_board = self._create_board(team_id, name="open-board")
        closed_board = self._create_board(team_id, name="closed-board")
        self.board_api.close_board(json.dumps({"id": closed_board}))

        boards = json.loads(self.board_api.list_boards(json.dumps({"id": team_id})))

        self.assertEqual(len(boards), 1)
        self.assertEqual(boards[0]["id"], open_board)

    def test_list_boards_empty_team_returns_empty_list(self):
        team_id, _ = self._create_team()
        boards = json.loads(self.board_api.list_boards(json.dumps({"id": team_id})))
        self.assertEqual(boards, [])

    def test_list_boards_nonexistent_team_raises(self):
        with self.assertRaises(NotFoundError):
            self.board_api.list_boards(json.dumps({"id": "nonexistent"}))


if __name__ == "__main__":
    unittest.main()