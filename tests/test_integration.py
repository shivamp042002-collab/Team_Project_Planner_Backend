import json
import shutil
import tempfile
import unittest
from pathlib import Path

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


class FullLifecycleIntegrationTest(unittest.TestCase):
    """Exercises every module together in one continuous scenario, the way
    a real client would: create people, form a team, run a board through
    its full lifecycle, and export it."""

    def setUp(self):
        self._tmp_dir = Path(tempfile.mkdtemp())
        self._out_dir = self._tmp_dir / "out"

        user_repo = UserRepository(db_dir=self._tmp_dir)
        team_repo = TeamRepository(db_dir=self._tmp_dir)
        board_repo = BoardRepository(db_dir=self._tmp_dir)
        task_repo = TaskRepository(db_dir=self._tmp_dir)

        self.user_api = UserApi(user_service=UserService(user_repository=user_repo, team_repository=team_repo))
        self.team_api = TeamApi(team_service=TeamService(team_repository=team_repo, user_repository=user_repo))
        self.board_api = BoardApi(board_service=BoardService(
            board_repository=board_repo, team_repository=team_repo,
            task_repository=task_repo, user_repository=user_repo,
            out_dir=self._out_dir,
        ))

    def tearDown(self):
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def test_full_project_lifecycle(self):
        # 1. Create users
        alice = json.loads(self.user_api.create_user(
            json.dumps({"name": "alice", "display_name": "Alice A."})
        ))["id"]
        bob = json.loads(self.user_api.create_user(
            json.dumps({"name": "bob", "display_name": "Bob B."})
        ))["id"]

        # 2. Alice creates a team and adds Bob
        team_id = json.loads(self.team_api.create_team(
            json.dumps({"name": "platform-team", "description": "core platform", "admin": alice})
        ))["id"]
        self.team_api.add_users_to_team(json.dumps({"id": team_id, "users": [bob]}))

        members = json.loads(self.team_api.list_team_users(json.dumps({"id": team_id})))
        self.assertEqual({m["id"] for m in members}, {alice, bob})

        # 3. Bob shows up in alice's + his own team list
        alice_teams = json.loads(self.user_api.get_user_teams(json.dumps({"id": alice})))
        bob_teams = json.loads(self.user_api.get_user_teams(json.dumps({"id": bob})))
        self.assertEqual(len(alice_teams), 1)
        self.assertEqual(len(bob_teams), 1)

        # 4. Create a board for the team
        board_id = json.loads(self.board_api.create_board(
            json.dumps({"name": "sprint-1", "description": "first sprint", "team_id": team_id})
        ))["id"]

        boards = json.loads(self.board_api.list_boards(json.dumps({"id": team_id})))
        self.assertEqual(len(boards), 1)

        # 5. Add two tasks, assign to Bob
        task1 = json.loads(self.board_api.add_task(
            json.dumps({"title": "design-api", "description": "draft the API", "user_id": bob, "board_id": board_id})
        ))["id"]
        task2 = json.loads(self.board_api.add_task(
            json.dumps({"title": "write-tests", "description": "cover edge cases", "user_id": bob, "board_id": board_id})
        ))["id"]

        # 6. Board can't close yet — tasks still OPEN
        with self.assertRaises(Exception):
            self.board_api.close_board(json.dumps({"id": board_id}))

        # 7. Move tasks through their lifecycle
        self.board_api.update_task_status(json.dumps({"id": task1, "status": "IN_PROGRESS"}))
        self.board_api.update_task_status(json.dumps({"id": task1, "status": "COMPLETE"}))
        self.board_api.update_task_status(json.dumps({"id": task2, "status": "COMPLETE"}))

        # 8. Now the board can close
        self.board_api.close_board(json.dumps({"id": board_id}))

        # 9. Closed boards no longer appear in list_boards (OPEN only)
        boards_after_close = json.loads(self.board_api.list_boards(json.dumps({"id": team_id})))
        self.assertEqual(boards_after_close, [])

        # 10. Export produces a file mentioning both completed tasks
        export_response = json.loads(self.board_api.export_board(json.dumps({"id": board_id})))
        out_file = self._out_dir / export_response["out_file"]
        self.assertTrue(out_file.exists())
        content = out_file.read_text()
        self.assertIn("design-api", content)
        self.assertIn("write-tests", content)
        self.assertIn("Bob B.", content)
        self.assertIn("CLOSED", content)


if __name__ == "__main__":
    unittest.main()