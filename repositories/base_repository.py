import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_DIR = PROJECT_ROOT / "db"


class BaseRepository:

    def __init__(self, entity_name: str, db_dir: Optional[Path] = None):
        self._db_dir = db_dir or DB_DIR
        self._db_dir.mkdir(parents=True, exist_ok=True)
        self._file_path = self._db_dir / f"{entity_name}.json"

    #  low-level file access

    def _load(self) -> list:
        if not self._file_path.exists():
            return []
        with open(self._file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)

    def _save(self, records: list) -> None:
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

    # generic CRUD helper

    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())

    def get_all(self) -> list:
        return self._load()

    def get_by_id(self, record_id: str) -> Optional[dict]:
        for record in self._load():
            if record.get("id") == record_id:
                return record
        return None

    def find(self, **filters) -> list:
        records = self._load()
        return [
            r for r in records
            if all(r.get(k) == v for k, v in filters.items())
        ]

    def add(self, record: dict) -> dict:
        records = self._load()
        records.append(record)
        self._save(records)
        return record

    def update(self, record_id: str, updated_fields: dict) -> Optional[dict]:
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
        records = self._load()
        remaining = [r for r in records if r.get("id") != record_id]
        if len(remaining) == len(records):
            return False
        self._save(remaining)
        return True
