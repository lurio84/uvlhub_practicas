"""Service-level tests for the notepad feature.

These exercise services and repositories against a real database, without
going through the HTTP layer. Use the ``test_app`` fixture (provides an app
context + reset DB) from splent_framework.
"""
import pytest

from app.features.auth.repositories import UserRepository
from app.features.notepad.services import NotepadService

pytestmark = pytest.mark.service


def test_get_all_by_user_only_returns_own_notepads(test_app, clean_database):
    with test_app.app_context():
        service = NotepadService()
        mine = UserRepository().create(email="mine@example.com", password="secret")
        theirs = UserRepository().create(email="theirs@example.com", password="secret")
        service.create(title="Mine", body="...", user_id=mine.id)
        service.create(title="Theirs", body="...", user_id=theirs.id)

        notepads = service.get_all_by_user(mine.id)

        assert [n.title for n in notepads] == ["Mine"]


def test_update_changes_title_and_body(test_app, clean_database):
    with test_app.app_context():
        service = NotepadService()
        user = UserRepository().create(email="ada@example.com", password="secret")
        notepad = service.create(title="Old", body="old body", user_id=user.id)

        service.update(notepad.id, title="New", body="new body")

        updated = service.get_by_id(notepad.id)
        assert (updated.title, updated.body) == ("New", "new body")


def test_delete_removes_notepad_and_reports_missing_id(test_app, clean_database):
    with test_app.app_context():
        service = NotepadService()
        user = UserRepository().create(email="ada@example.com", password="secret")
        notepad = service.create(title="Bye", body="...", user_id=user.id)

        assert service.delete(notepad.id) is True
        assert service.get_by_id(notepad.id) is None
        assert service.delete(notepad.id) is False
