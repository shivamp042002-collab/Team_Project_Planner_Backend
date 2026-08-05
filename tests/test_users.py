import json
import shutil
import tempfile
import unittest
from pathlib import Path

from exceptions.errors import ConflictError, NotFoundError, ValidationError
from repositories.user_repository import UserRepository
from services.user_service import UserService
from users.api import UserApi


class UserApiTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.mkdtemp()
        repo = UserRepository(db_dir=Path(self._tmp_dir))
        service = UserService(user_repository=repo)
        self.api = UserApi(user_service=service)

    def tearDown(self):
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def _create_user(self, name="alice", display_name="Alice A."):
        response = self.api.create_user(
            json.dumps({"name": name, "display_name": display_name})
        )
        return json.loads(response)["id"]

    # create_user 

    def test_create_user_valid_returns_id(self):
        response = self.api.create_user(
            json.dumps({"name": "alice", "display_name": "Alice A."})
        )
        data = json.loads(response)
        self.assertIn("id", data)
        self.assertTrue(len(data["id"]) > 0)

    def test_create_user_duplicate_name_raises_conflict(self):
        self._create_user(name="alice")
        with self.assertRaises(ConflictError):
            self.api.create_user(
                json.dumps({"name": "alice", "display_name": "Someone Else"})
            )

    def test_create_user_name_too_long_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.api.create_user(
                json.dumps({"name": "a" * 65, "display_name": "Alice"})
            )

    def test_create_user_display_name_too_long_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.api.create_user(
                json.dumps({"name": "alice", "display_name": "a" * 65})
            )

    def test_create_user_missing_name_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.api.create_user(json.dumps({"display_name": "Alice"}))

    # list_users

    def test_list_users_empty(self):
        response = self.api.list_users()
        self.assertEqual(json.loads(response), [])

    def test_list_users_returns_multiple(self):
        self._create_user(name="alice")
        self._create_user(name="bob")

        response = self.api.list_users()
        data = json.loads(response)

        self.assertEqual(len(data), 2)
        self.assertEqual({u["name"] for u in data}, {"alice", "bob"})

    # describe_user 

    def test_describe_user_found(self):
        user_id = self._create_user(name="alice", display_name="Alice A.")

        response = self.api.describe_user(json.dumps({"id": user_id}))
        data = json.loads(response)

        self.assertEqual(data["name"], "alice")
        self.assertEqual(data["display_name"], "Alice A.")
        self.assertIn("creation_time", data)

    def test_describe_user_not_found_raises(self):
        with self.assertRaises(NotFoundError):
            self.api.describe_user(json.dumps({"id": "nonexistent"}))

    # update_user 

    def test_update_user_valid_display_name(self):
        user_id = self._create_user(name="alice", display_name="Alice A.")

        response = self.api.update_user(
            json.dumps({"id": user_id, "user": {"display_name": "Alice B."}})
        )
        data = json.loads(response)

        self.assertEqual(data["display_name"], "Alice B.")
        self.assertEqual(data["name"], "alice")  # unchanged

    def test_update_user_attempt_to_change_name_raises(self):
        user_id = self._create_user(name="alice", display_name="Alice A.")

        with self.assertRaises(ValidationError):
            self.api.update_user(
                json.dumps(
                    {
                        "id": user_id,
                        "user": {"name": "someone_else", "display_name": "Alice A."},
                    }
                )
            )

    def test_update_user_not_found_raises(self):
        with self.assertRaises(NotFoundError):
            self.api.update_user(
                json.dumps(
                    {"id": "nonexistent", "user": {"display_name": "New Name"}}
                )
            )

    def test_update_user_display_name_too_long_raises(self):
        user_id = self._create_user(name="alice", display_name="Alice A.")

        with self.assertRaises(ValidationError):
            self.api.update_user(
                json.dumps({"id": user_id, "user": {"display_name": "a" * 129}})
            )


if __name__ == "__main__":
    unittest.main()