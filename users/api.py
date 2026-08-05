import json
from services.user_service import UserService
from user_base import UserBase


class UserApi(UserBase):
    def __init__(self, user_service: UserService = None):
        self._service = user_service or UserService()

    def create_user(self, request: str) -> str:
        data = json.loads(request)
        user = self._service.create_user(
            name=data.get("name"),
            display_name=data.get("display_name"),
        )
        return json.dumps({"id": user["id"]})

    def list_users(self) -> str:
        users = self._service.list_users()
        return json.dumps(users)

    def describe_user(self, request: str) -> str:
        data = json.loads(request)
        user = self._service.describe_user(user_id=data.get("id"))
        return json.dumps(user)

    def update_user(self, request: str) -> str:
        data = json.loads(request)
        user_fields = data.get("user", {})
        updated = self._service.update_user(
            user_id=data.get("id"),
            name=user_fields.get("name"),
            display_name=user_fields.get("display_name"),
        )
        return json.dumps(updated)

    def get_user_teams(self, request: str) -> str:
        data = json.loads(request)
        teams = self._service.get_user_teams(user_id=data.get("id"))
        return json.dumps(teams)