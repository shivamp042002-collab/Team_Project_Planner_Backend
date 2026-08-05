from datetime import datetime, timezone

from exceptions.errors import ConflictError, NotFoundError, ValidationError
from repositories.team_repository import TeamRepository
from repositories.user_repository import UserRepository
from teams.models import Team
from validators.common import validate_max_length, validate_required

NAME_MAX_LENGTH = 64
DESCRIPTION_MAX_LENGTH = 128
MAX_USERS_PER_OPERATION = 50


class TeamService:
    def __init__(self, team_repository: TeamRepository = None, user_repository: UserRepository = None):
        self._teams = team_repository or TeamRepository()
        self._users = user_repository or UserRepository()

    def _get_team_or_raise(self, team_id: str) -> dict:
        team = self._teams.get_by_id(team_id)
        if team is None:
            raise NotFoundError(f"No team found with id '{team_id}'")
        return team

    def _validate_admin_exists(self, admin_id: str):
        if self._users.get_by_id(admin_id) is None:
            raise ValidationError(f"admin user '{admin_id}' does not exist")

    def create_team(self, name: str, description: str, admin: str) -> dict:
        validate_required(name, "name")
        validate_required(description, "description")
        validate_required(admin, "admin")
        validate_max_length(name, NAME_MAX_LENGTH, "name")
        validate_max_length(description, DESCRIPTION_MAX_LENGTH, "description")

        if self._teams.get_by_name(name) is not None:
            raise ConflictError(f"A team with name '{name}' already exists")
        self._validate_admin_exists(admin)

        team = Team(
            id=TeamRepository.generate_id(),
            name=name,
            description=description,
            admin=admin,
            creation_time=datetime.now(timezone.utc).isoformat(),
            member_ids=[admin],
        )
        self._teams.add(team.to_dict())
        return team.to_dict()

    def list_teams(self) -> list:
        return self._teams.get_all()

    def describe_team(self, team_id: str) -> dict:
        return self._get_team_or_raise(team_id)

    def update_team(self, team_id: str, name: str, description: str, admin: str) -> dict:
        team = self._get_team_or_raise(team_id)

        validate_required(name, "name")
        validate_required(description, "description")
        validate_max_length(name, NAME_MAX_LENGTH, "name")
        validate_max_length(description, DESCRIPTION_MAX_LENGTH, "description")

        existing = self._teams.get_by_name(name)
        if existing is not None and existing["id"] != team_id:
            raise ConflictError(f"A team with name '{name}' already exists")

        updated_fields = {"name": name, "description": description}
        if admin is not None:
            self._validate_admin_exists(admin)
            updated_fields["admin"] = admin
            if admin not in team["member_ids"]:
                updated_fields["member_ids"] = team["member_ids"] + [admin]

        return self._teams.update(team_id, updated_fields)

    def add_users_to_team(self, team_id: str, user_ids: list):
        team = self._get_team_or_raise(team_id)
        if not user_ids:
            raise ValidationError("'users' must be a non-empty list")
        if len(user_ids) > MAX_USERS_PER_OPERATION:
            raise ValidationError(f"cannot add more than {MAX_USERS_PER_OPERATION} users in a single call")

        for user_id in user_ids:
            if self._users.get_by_id(user_id) is None:
                raise NotFoundError(f"No user found with id '{user_id}'")

        merged = list(dict.fromkeys(team["member_ids"] + user_ids))
        self._teams.update(team_id, {"member_ids": merged})

    def remove_users_from_team(self, team_id: str, user_ids: list):
        team = self._get_team_or_raise(team_id)
        if not user_ids:
            raise ValidationError("'users' must be a non-empty list")
        if len(user_ids) > MAX_USERS_PER_OPERATION:
            raise ValidationError(f"cannot remove more than {MAX_USERS_PER_OPERATION} users in a single call")
        if team["admin"] in user_ids:
            raise ValidationError("cannot remove the team admin; reassign admin via update_team first")

        remaining = [uid for uid in team["member_ids"] if uid not in user_ids]
        self._teams.update(team_id, {"member_ids": remaining})

    def list_team_users(self, team_id: str) -> list:
        team = self._get_team_or_raise(team_id)
        users = []
        for user_id in team["member_ids"]:
            user = self._users.get_by_id(user_id)
            if user is not None:
                users.append(user)
        return users