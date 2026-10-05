"""Unit tests for the notepad feature.

Pure logic only — no Flask app, no database. Anything that needs persistence
or the test client belongs in test_service.py or test_integration.py.
"""
import pytest

from app.features.auth.models import User
from app.features.notepad.models import Notepad

pytestmark = pytest.mark.unit


def test_notepad_repr_shows_id_title_and_author_email():
    notepad = Notepad(id=1, title="Shopping", body="milk", user=User(email="ada@example.com"))

    assert repr(notepad) == "Notepad<1, Title=Shopping, Author=ada@example.com>"
