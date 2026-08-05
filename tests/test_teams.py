import json
import shutil
import tempfile
import unittest
from pathlib import Path

from exceptions.errors import ConflictError, NotFoundError, ValidationError
from repositories.team_repository import TeamRepository
from repositories.user_repository import UserRepository
from services.team_service import TeamService
from services.user_service import UserService
from teams.api import TeamApi
from users.api import UserApi


class TeamApiTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = Path(tempfile.mkdtemp())
        self.user_repo = UserRepository(db_dir=self._tmp_dir)
        self.team_repo = TeamRepository(db_dir=self._tmp_dir)
        self.user_api = UserApi(user_service=UserService(user_repository=self.user_repo, team_repository=self.team_repo))
        self.team_api = TeamApi(team_service=TeamService(team_repository=self.team_repo, user_repository=self.user_repo))

    def tearDown(self):
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def _create_user(self, name):
        response = self.user_api.create_user(json.dumps({"name": name, "display_name": name}))
        return json.loads(response)["id"]

    def _create_team(self, name="engineering", admin=None):
        admin = admin or self._create_user("admin_user")
        response = self.team_api.create_team(
            json.dumps({"name": name, "description": "desc", "admin": admin})
        )
        return json.loads(response)["id"], admin

    # create_team

    def test_create_team_valid_returns_id(self):
        team_id, _ = self._create_team()
        self.assertTrue(len(team_id) > 0)

    def test_create_team_duplicate_name_raises_conflict(self):
        self._create_team(name="engineering")
        with self.assertRaises(ConflictError):
            self._create_team(name="engineering")

    def test_create_team_invalid_admin_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.team_api.create_team(
                json.dumps({"name": "engineering", "description": "desc", "admin": "nonexistent"})
            )

    def test_create_team_name_too_long_raises(self):
        admin = self._create_user("admin_user")
        with self.assertRaises(ValidationError):
            self.team_api.create_team(
                json.dumps({"name": "a" * 65, "description": "desc", "admin": admin})
            )

    # describe_team / list_teams

    def test_describe_team_not_found_raises(self):
        with self.assertRaises(NotFoundError):
            self.team_api.describe_team(json.dumps({"id": "nonexistent"}))

    def test_list_teams_returns_created_team(self):
        self._create_team(name="engineering")
        data = json.loads(self.team_api.list_teams())
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "engineering")

    # add_users_to_team / remove_users_from_team 

    def test_add_users_to_team_valid(self):
        team_id, admin = self._create_team()
        user2 = self._create_user("bob")

        self.team_api.add_users_to_team(json.dumps({"id": team_id, "users": [user2]}))

        members = json.loads(self.team_api.list_team_users(json.dumps({"id": team_id})))
        self.assertEqual({m["id"] for m in members}, {admin, user2})

    def test_add_users_to_team_nonexistent_user_raises(self):
        team_id, _ = self._create_team()
        with self.assertRaises(NotFoundError):
            self.team_api.add_users_to_team(json.dumps({"id": team_id, "users": ["nonexistent"]}))

    def test_add_users_to_team_over_cap_raises(self):
        team_id, _ = self._create_team()
        with self.assertRaises(ValidationError):
            self.team_api.add_users_to_team(
                json.dumps({"id": team_id, "users": [f"u{i}" for i in range(51)]})
            )

    def test_remove_admin_from_team_raises(self):
        team_id, admin = self._create_team()
        with self.assertRaises(ValidationError):
            self.team_api.remove_users_from_team(json.dumps({"id": team_id, "users": [admin]}))

    def test_remove_users_from_team_valid(self):
        team_id, admin = self._create_team()
        user2 = self._create_user("bob")
        self.team_api.add_users_to_team(json.dumps({"id": team_id, "users": [user2]}))

        self.team_api.remove_users_from_team(json.dumps({"id": team_id, "users": [user2]}))

        members = json.loads(self.team_api.list_team_users(json.dumps({"id": team_id})))
        self.assertEqual({m["id"] for m in members}, {admin})

    # get_user_teams

    def test_get_user_teams_returns_teams_for_member(self):
        team_id, admin = self._create_team(name="engineering")

        teams = json.loads(self.user_api.get_user_teams(json.dumps({"id": admin})))

        self.assertEqual(len(teams), 1)
        self.assertEqual(teams[0]["id"], team_id)

    def test_get_user_teams_empty_when_no_membership(self):
        user_id = self._create_user("lonely_user")
        teams = json.loads(self.user_api.get_user_teams(json.dumps({"id": user_id})))
        self.assertEqual(teams, [])

    def test_get_user_teams_nonexistent_user_raises(self):
        with self.assertRaises(NotFoundError):
            self.user_api.get_user_teams(json.dumps({"id": "nonexistent"}))


if __name__ == "__main__":
    unittest.main()