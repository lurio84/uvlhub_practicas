"""HTTP integration tests for the notepad feature.

Drive the application through the Flask test client. The ``test_client``
fixture from splent_framework rebuilds a clean DB per test for full isolation.
"""
import pytest

from app.features.notepad.models import Notepad

pytestmark = pytest.mark.integration


def signup(test_client, email="ada@example.com"):
    """Register and log in a user (CSRF is disabled under testing)."""
    return test_client.post(
        "/signup/",
        data={"email": email, "password": "secret123", "name": "Ada", "surname": "Lovelace"},
        follow_redirects=False,
    )


def create_notepad(test_client, title="Shopping", body="milk"):
    return test_client.post(
        "/notepad/create",
        data={"title": title, "body": body},
        follow_redirects=True,
    )


def test_notepad_index_requires_login(test_client):
    response = test_client.get("/notepad", follow_redirects=False)

    assert response.status_code in (302, 303)
    assert "/login" in response.headers["Location"]


def test_create_notepad_shows_it_in_the_list(test_client):
    signup(test_client)

    response = create_notepad(test_client, title="Shopping", body="milk")

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Notepad created successfully!" in body
    assert "Shopping" in body


def test_create_notepad_with_empty_title_is_rejected(test_app, test_client):
    signup(test_client)

    response = create_notepad(test_client, title="", body="milk")

    assert response.status_code == 200
    assert "This field is required." in response.get_data(as_text=True)
    with test_app.app_context():
        assert Notepad.query.count() == 0


def test_unknown_notepad_returns_404(test_client):
    signup(test_client)

    response = test_client.get("/notepad/999")

    assert response.status_code == 404


def test_user_cannot_view_another_users_notepad(test_app, test_client):
    signup(test_client, email="ada@example.com")
    create_notepad(test_client, title="Ada's secret")
    with test_app.app_context():
        notepad_id = Notepad.query.one().id
    test_client.get("/logout")
    signup(test_client, email="bob@example.com")

    response = test_client.get(f"/notepad/{notepad_id}", follow_redirects=True)

    body = response.get_data(as_text=True)
    assert "You are not authorized to view this notepad" in body
    assert "Ada's secret" not in body


def test_edit_notepad_updates_it(test_app, test_client):
    signup(test_client)
    create_notepad(test_client, title="Old")
    with test_app.app_context():
        notepad_id = Notepad.query.one().id

    response = test_client.post(
        f"/notepad/edit/{notepad_id}",
        data={"title": "New", "body": "new body"},
        follow_redirects=True,
    )

    body = response.get_data(as_text=True)
    assert "Notepad updated successfully!" in body
    assert "New" in body


def test_delete_notepad_removes_it(test_app, test_client):
    signup(test_client)
    create_notepad(test_client, title="Bye")
    with test_app.app_context():
        notepad_id = Notepad.query.one().id

    response = test_client.post(f"/notepad/delete/{notepad_id}", follow_redirects=True)

    assert "Notepad deleted successfully!" in response.get_data(as_text=True)
    with test_app.app_context():
        assert Notepad.query.count() == 0
