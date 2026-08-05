"""
Base repository providing generic JSON-file-backed CRUD operations.

This is the only layer in the application that touches the filesystem.
Concrete repositories (UserRepository, TeamRepository, ...) subclass this
and only need to supply an entity name; all load/save/atomic-write/id
generation logic lives here so it isn't duplicated per entity.

Storage format: one JSON file per entity under db/<entity_name>.json,
each holding a JSON array of plain dicts (records).
"""
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional

# Project root is two levels up from this file (repositories/base_repository.py).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_DIR = PROJECT_ROOT / "db"


class BaseRepository:
    """Generic JSON-file-backed repository for a single entity type."""

    def __init__(self, entity_name: str, db_dir: Optional[Path] = None):
        """
        :param entity_name: logical name of the entity, used as the JSON
            filename (e.g. "users" -> db/users.json)
        :param db_dir: override for the storage directory (used in tests
            to avoid touching the real db/ folder)
        """
        self._db_dir = db_dir or DB_DIR
        self._db_dir.mkdir(parents=True, exist_ok=True)
        self._file_path = self._db_dir / f"{entity_name}.json"

    # -- low-level file access -------------------------------------------------

    def _load(self) -> list:
        """Load all records from disk. Returns [] if the file doesn't exist
        yet or is empty."""
        if not self._file_path.exists():
            return []
        with open(self._file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)

    def _save(self, records: list) -> None:
        """Persist all records atomically: write to a temp file in the same
        directory, then os.replace() onto the real file. This guarantees
        the real file is never left partially written if the process is
        interrupted mid-save."""
        fd, tmp_path = tempfile.mkstemp(
            dir=self._db_dir, prefix=".tmp_", suffix=".json"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(records, tmp_file, indent=2)
            os.replace(tmp_path, self._file_path)
        except BaseException:
            # Clean up the temp file if something went wrong before replace.
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    # -- generic CRUD helpers ---------------------------------------------------

    @staticmethod
    def generate_id() -> str:
        """Generate a new unique id for a record."""
        return str(uuid.uuid4())

    def get_all(self) -> list:
        """Return all records for this entity."""
        return self._load()

    def get_by_id(self, record_id: str) -> Optional[dict]:
        """Return the record with the given id, or None if not found."""
        for record in self._load():
            if record.get("id") == record_id:
                return record
        return None

    def find(self, **filters) -> list:
        """Return all records matching the given field=value filters."""
        records = self._load()
        return [
            r for r in records
            if all(r.get(k) == v for k, v in filters.items())
        ]

    def add(self, record: dict) -> dict:
        """Append a new record (assumed to already contain an 'id') and
        persist it. Returns the record as stored."""
        records = self._load()
        records.append(record)
        self._save(records)
        return record

    def update(self, record_id: str, updated_fields: dict) -> Optional[dict]:
        """Merge updated_fields into the record with the given id and
        persist. Returns the updated record, or None if no record with
        that id exists."""
        records = self._load()
        updated_record = None
        for record in records:
            if record.get("id") == record_id:
                record.update(updated_fields)
                updated_record = record
                break
        if updated_record is not None:
            self._save(records)
        return updated_record

    def delete(self, record_id: str) -> bool:
        """Remove the record with the given id. Returns True if a record
        was removed, False if no matching record was found."""
        records = self._load()
        remaining = [r for r in records if r.get("id") != record_id]
        if len(remaining) == len(records):
            return False
        self._save(remaining)
        return True
