"""Repository-level tests for the notepad feature.

These exercise the repository in isolation against a real database — no
service orchestration, no HTTP. Use the ``test_app`` fixture from
splent_framework for the app context and a fresh DB.
"""
import pytest

from app.features.auth.repositories import UserRepository
from app.features.notepad.repositories import NotepadRepository

pytestmark = pytest.mark.repository


def test_get_all_by_user_filters_by_owner(test_app, clean_database):
    with test_app.app_context():
        repo = NotepadRepository()
        ada = UserRepository().create(email="ada@example.com", password="secret")
        bob = UserRepository().create(email="bob@example.com", password="secret")
        repo.create(title="Ada 1", body="...", user_id=ada.id)
        repo.create(title="Ada 2", body="...", user_id=ada.id)
        repo.create(title="Bob 1", body="...", user_id=bob.id)

        titles = sorted(n.title for n in repo.get_all_by_user(ada.id))

        assert titles == ["Ada 1", "Ada 2"]


def test_get_all_by_user_without_notepads_returns_empty_list(test_app, clean_database):
    with test_app.app_context():
        ada = UserRepository().create(email="ada@example.com", password="secret")

        assert NotepadRepository().get_all_by_user(ada.id) == []
