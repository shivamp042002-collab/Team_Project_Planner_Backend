# Team Project Planner — Backend

Django-based backend for managing users, teams, and project boards. Implements the HR-provided abstract interfaces (`UserBase`, `TeamBase`, `ProjectBoardBase`) as plain Python classes with JSON string I/O, backed by local file storage.

## Contents

- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Running Tests](#running-tests)
- [Persistence](#persistence)
- [API Usage](#api-usage)
- [Assumptions](#assumptions)
- [Design Decisions](#design-decisions)
- [Future Improvements](#future-improvements)

## Architecture

Three layers, one direction of dependency:

```
Api        implements UserBase / TeamBase / ProjectBoardBase
           parses request JSON, serializes response JSON
             │
Service    business rules — validation, uniqueness, state
           transitions, cross-entity checks
             │
Repository file I/O only — atomic JSON read/write
             │
db/*.json
```

Api classes contain no business logic. Services never touch the filesystem. Repositories know nothing about JSON request/response shapes — they operate on plain dicts. This keeps each layer independently testable and means a storage backend change (e.g. SQLite) touches only the repository layer.

Cross-entity checks — e.g. does `user_id` exist when adding a task — call the other entity's repository directly, not its service. These are existence lookups, not business rules, so routing through a full service adds indirection without benefit.

## Project Structure

```
config/                 Django settings (no ORM, no views — not needed)
user_base.py            HR-provided interface, unmodified
team_base.py            HR-provided interface, unmodified
project_board_base.py   HR-provided interface, unmodified
users/
  api.py                 UserApi(UserBase)
  models.py               User dataclass
teams/
  api.py                 TeamApi(TeamBase)
  models.py               Team dataclass
boards/
  api.py                 BoardApi(ProjectBoardBase)
  models.py               Board, Task dataclasses
services/
  user_service.py
  team_service.py
  board_service.py
repositories/
  base_repository.py     shared load/save/atomic-write/id generation
  user_repository.py
  team_repository.py
  board_repository.py
  task_repository.py
validators/
  common.py               required / max-length / choice validators
exceptions/
  errors.py               AppError, ValidationError, NotFoundError,
                          ConflictError, InvalidStateError
tests/                    one test module per Api + one integration test
db/                       JSON data files (gitignored, auto-created)
out/                      board export .txt files (gitignored)
```

## Setup

```bash
pip install -r requirements.txt
python manage.py check
```

No `.env` or database configuration required — persistence is file-based, and `config/settings.py` carries only what Django's framework needs to run.

## Running Tests

```bash
python manage.py test tests
```

73 tests: unit coverage per module (create/list/describe/update, validation failures, not-found, conflict, state-transition errors) plus one full lifecycle integration test — user → team → board → tasks → close → export — in `tests/test_integration.py`.

## Persistence

One JSON file per entity under `db/`: `users.json`, `teams.json`, `boards.json`, `tasks.json`. Created on first write. Every write is atomic — written to a temp file in the same directory, then moved into place with `os.replace()` — so a crash mid-write cannot corrupt existing data.

`db/` and `out/` are gitignored except for `.gitkeep` placeholders; no data files are committed.

## API Usage

Every method takes and returns a JSON string, per the base class contracts:

```python
from users.api import UserApi
import json

api = UserApi()
response = api.create_user(json.dumps({
    "name": "alice",
    "display_name": "Alice A.",
}))
user_id = json.loads(response)["id"]
```

Full request/response shapes and constraints are documented in `user_base.py`, `team_base.py`, and `project_board_base.py`. Implementations follow those docstrings exactly, except where noted below.

## Assumptions

A few base-class docstrings were ambiguous or contained apparent copy-paste errors. Decisions taken:

**`describe_user`** returns `id`, `name`, `display_name`, `creation_time`. The docstring's sample includes a `description` field that has no corresponding data anywhere on `User` — it appears copied from `describe_team`.

**`list_users`** includes `id` in each entry, though the docstring sample omits it. Without an id a caller has no way to reference a user in any subsequent call.

**`list_boards`** returns only `OPEN` boards. The method's inline comment says "list all open boards"; the docstring body doesn't restate the filter but this is the more specific signal.

**`add_task`** reads a `board_id` field from the request, which the docstring doesn't list. A task must be attached to a board somehow; the sample request appears to be missing this field.

**Task status transitions** are unrestricted — any status to any other. The interface defines three values and no ordering constraint between them.

**The 50-user cap** on `add_users_to_team` / `remove_users_from_team` is enforced per call, not as a total team-size ceiling — the constraint reads as a per-request limit.

**Removing a team's admin** via `remove_users_from_team` is rejected. A team must always have an admin; reassignment happens through `update_team`.

**Closing a board with zero tasks** succeeds — "all tasks marked COMPLETE" is vacuously true when there are none.

**All entity ids** are server-generated UUIDs. No `create_*` request schema accepts a client-supplied id.

## Design Decisions

**JSON files over SQLite.** No added dependency, and every record is human-readable during review. The tradeoff — no transactions, no indices — doesn't matter at this scale.

**No HTTP layer.** The base classes define a JSON-string method contract, not an HTTP one. Django is used for its project scaffold; `INSTALLED_APPS` and `DATABASES` are left empty since nothing here uses the ORM.

**Service layer separated from Api layer.** Keeps each `*Api` class a thin, auditable adapter matching the HR interface verbatim, and lets business logic be tested without JSON parsing in the way.

## Future Improvements

- Swap `BaseRepository`'s per-entity JSON files for SQLite if concurrent writes or dataset size become a concern — repository layer is the only thing that would change.
- Paginate `list_users` / `list_teams` / `list_boards` once entity counts grow.
- Add a thin Django REST layer if this needs to serve a non-Python client.
