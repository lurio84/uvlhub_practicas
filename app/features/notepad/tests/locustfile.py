from locust import HttpUser, TaskSet, between, task

from splent_framework.environment.host import get_host_for_locust_testing
from splent_framework.locust.common import get_csrf_token

# Seeded account. Only read traffic is issued on its behalf, it is never mutated.
SEEDED_EMAIL = "user1@example.com"
SEEDED_PASSWORD = "1234"


class NotepadBehavior(TaskSet):
    """Browsing traffic over the notepad feature for a logged-in user.

    Every route is behind @login_required, so without logging in in on_start
    each request would silently land on /login and look healthy.

    Deliberately excluded, because they mutate state on a shared dev database:
    POST /notepad/create, /notepad/edit/<id> and /notepad/delete/<id>.
    """

    def on_start(self):
        self.login()

    def login(self):
        response = self.client.get("/login", name="/login [GET]")
        try:
            csrf_token = get_csrf_token(response)
        except ValueError:
            print("Could not read the CSRF token from the login form")
            return

        response = self.client.post(
            "/login",
            name="/login [POST]",
            data={
                "email": SEEDED_EMAIL,
                "password": SEEDED_PASSWORD,
                "csrf_token": csrf_token,
            },
        )
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")

    def get_logged_in(self, path, name):
        """GET a protected page and fail the request if it bounced to /login."""
        with self.client.get(path, name=name, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"{path} returned {response.status_code}")
            elif "/login" in response.url:
                response.failure(f"{path} redirected to /login: not logged in")

    @task(3)
    def index(self):
        self.get_logged_in("/notepad", "/notepad")

    @task(1)
    def create_form(self):
        self.get_logged_in("/notepad/create", "/notepad/create [GET]")


class NotepadUser(HttpUser):
    tasks = [NotepadBehavior]
    wait_time = between(1, 3)
    host = get_host_for_locust_testing()
