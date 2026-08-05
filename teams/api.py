import json

from services.team_service import TeamService
from team_base import TeamBase


class TeamApi(TeamBase):
    def __init__(self, team_service: TeamService = None):
        self._service = team_service or TeamService()

    def create_team(self, request: str) -> str:
        data = json.loads(request)
        team = self._service.create_team(
            name=data.get("name"),
            description=data.get("description"),
            admin=data.get("admin"),
        )
        return json.dumps({"id": team["id"]})

    def list_teams(self) -> str:
        return json.dumps(self._service.list_teams())

    def describe_team(self, request: str) -> str:
        data = json.loads(request)
        team = self._service.describe_team(team_id=data.get("id"))
        return json.dumps(team)

    def update_team(self, request: str) -> str:
        data = json.loads(request)
        team_fields = data.get("team", {})
        updated = self._service.update_team(
            team_id=data.get("id"),
            name=team_fields.get("name"),
            description=team_fields.get("description"),
            admin=team_fields.get("admin"),
        )
        return json.dumps(updated)

    def add_users_to_team(self, request: str):
        data = json.loads(request)
        self._service.add_users_to_team(team_id=data.get("id"), user_ids=data.get("users", []))

    def remove_users_from_team(self, request: str):
        data = json.loads(request)
        self._service.remove_users_from_team(team_id=data.get("id"), user_ids=data.get("users", []))

    def list_team_users(self, request: str):
        data = json.loads(request)
        users = self._service.list_team_users(team_id=data.get("id"))
        return json.dumps(users)