from datetime import datetime, timezone
from exceptions.errors import ConflictError, NotFoundError, ValidationError
from repositories.user_repository import UserRepository
from users.models import User
from validators.common import validate_max_length, validate_required

NAME_MAX_LENGTH = 64
DISPLAY_NAME_MAX_LENGTH = 64
DISPLAY_NAME_UPDATE_MAX_LENGTH = 128


class UserService:
    def __init__(self, user_repository: UserRepository = None):
        self._users = user_repository or UserRepository()

    def create_user(self, name: str, display_name: str) -> dict:
        validate_required(name, "name")
        validate_required(display_name, "display_name")
        validate_max_length(name, NAME_MAX_LENGTH, "name")
        validate_max_length(display_name, DISPLAY_NAME_MAX_LENGTH, "display_name")

        if self._users.get_by_name(name) is not None:
            raise ConflictError(f"A user with name '{name}' already exists")

        user = User(
            id=UserRepository.generate_id(),
            name=name,
            display_name=display_name,
            creation_time=datetime.now(timezone.utc).isoformat(),
        )
        self._users.add(user.to_dict())
        return user.to_dict()

    def list_users(self) -> list:
        return self._users.get_all()

    def describe_user(self, user_id: str) -> dict:
        record = self._users.get_by_id(user_id)
        if record is None:
            raise NotFoundError(f"No user found with id '{user_id}'")
        return record

    def update_user(self, user_id: str, name: str, display_name: str) -> dict:
        record = self._users.get_by_id(user_id)
        if record is None:
            raise NotFoundError(f"No user found with id '{user_id}'")

        if name is not None and name != record["name"]:
            raise ValidationError("'name' cannot be updated once a user is created")

        validate_required(display_name, "display_name")
        validate_max_length(
            display_name, DISPLAY_NAME_UPDATE_MAX_LENGTH, "display_name"
        )

        updated = self._users.update(user_id, {"display_name": display_name})
        return updated

    def get_user_teams(self, user_id: str) -> list:
        record = self._users.get_by_id(user_id)
        if record is None:
            raise NotFoundError(f"No user found with id '{user_id}'")
        raise NotImplementedError(
            "get_user_teams will be implemented in Milestone 3 "
            "(requires TeamRepository)"
        )