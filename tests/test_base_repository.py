"""
Tests for repositories.base_repository.BaseRepository.

Each test uses a fresh temporary directory so these tests never touch the
project's real db/ folder and don't interfere with each other.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from repositories.base_repository import BaseRepository


class BaseRepositoryTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.mkdtemp()
        self.repo = BaseRepository("widgets", db_dir=Path(self._tmp_dir))

    def tearDown(self):
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def test_get_all_returns_empty_list_when_file_missing(self):
        self.assertEqual(self.repo.get_all(), [])

    def test_add_and_get_by_id_round_trip(self):
        self.repo.add({"id": "abc-123", "name": "Widget A"})

        fetched = self.repo.get_by_id("abc-123")

        self.assertEqual(fetched, {"id": "abc-123", "name": "Widget A"})

    def test_get_by_id_returns_none_when_not_found(self):
        self.assertIsNone(self.repo.get_by_id("does-not-exist"))

    def test_get_all_returns_all_added_records(self):
        self.repo.add({"id": "1", "name": "A"})
        self.repo.add({"id": "2", "name": "B"})

        all_records = self.repo.get_all()

        self.assertEqual(len(all_records), 2)
        self.assertEqual({r["id"] for r in all_records}, {"1", "2"})

    def test_find_filters_by_field(self):
        self.repo.add({"id": "1", "team_id": "t1", "name": "A"})
        self.repo.add({"id": "2", "team_id": "t2", "name": "B"})
        self.repo.add({"id": "3", "team_id": "t1", "name": "C"})

        results = self.repo.find(team_id="t1")

        self.assertEqual({r["id"] for r in results}, {"1", "3"})

    def test_update_merges_fields_and_persists(self):
        self.repo.add({"id": "1", "name": "Old Name", "status": "OPEN"})

        updated = self.repo.update("1", {"name": "New Name"})

        self.assertEqual(updated["name"], "New Name")
        self.assertEqual(updated["status"], "OPEN")  # untouched field preserved
        self.assertEqual(self.repo.get_by_id("1")["name"], "New Name")

    def test_update_returns_none_when_id_not_found(self):
        self.assertIsNone(self.repo.update("missing-id", {"name": "X"}))

    def test_delete_removes_record_and_returns_true(self):
        self.repo.add({"id": "1", "name": "A"})

        result = self.repo.delete("1")

        self.assertTrue(result)
        self.assertIsNone(self.repo.get_by_id("1"))

    def test_delete_returns_false_when_id_not_found(self):
        self.assertFalse(self.repo.delete("missing-id"))

    def test_generate_id_produces_unique_values(self):
        ids = {BaseRepository.generate_id() for _ in range(100)}
        self.assertEqual(len(ids), 100)

    def test_save_writes_valid_json_file_on_disk(self):
        self.repo.add({"id": "1", "name": "A"})

        file_path = Path(self._tmp_dir) / "widgets.json"
        self.assertTrue(file_path.exists())

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data, [{"id": "1", "name": "A"}])

    def test_repeated_saves_do_not_corrupt_or_lose_data(self):
        """Simulates repeated writes (as would happen across many API
        calls) and confirms every previously saved record survives each
        subsequent save (guarding against the atomic-write path losing
        data)."""
        for i in range(20):
            self.repo.add({"id": str(i), "name": f"Widget {i}"})

        all_records = self.repo.get_all()
        self.assertEqual(len(all_records), 20)
        self.assertEqual({r["id"] for r in all_records}, {str(i) for i in range(20)})


if __name__ == "__main__":
    unittest.main()
