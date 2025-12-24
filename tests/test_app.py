from copy import deepcopy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict after each test to avoid cross-test pollution."""
    original = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activities(client):
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Basketball" in data


def test_signup_for_activity_success(client):
    activity = "Chess Club"
    email = "newstudent@mergington.edu"

    # Ensure email is not already registered
    assert email not in activities[activity]["participants"]

    response = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert response.status_code == 200
    assert email in activities[activity]["participants"]
    assert response.json()["message"] == f"Signed up {email} for {activity}"


def test_signup_duplicate_returns_400(client):
    activity = "Chess Club"
    existing = activities[activity]["participants"][0]

    response = client.post(f"/activities/{activity}/signup", params={"email": existing})
    assert response.status_code == 400


def test_signup_activity_not_found_returns_404(client):
    response = client.post("/activities/NoSuchActivity/signup", params={"email": "a@b.com"})
    assert response.status_code == 404


def test_unregister_from_activity_success(client):
    activity = "Chess Club"
    existing = activities[activity]["participants"][0]

    response = client.delete(f"/activities/{activity}/participants", params={"email": existing})
    assert response.status_code == 200
    assert existing not in activities[activity]["participants"]
    assert response.json()["message"] == f"Unregistered {existing} from {activity}"


def test_unregister_nonexistent_participant_returns_404(client):
    activity = "Chess Club"
    response = client.delete(f"/activities/{activity}/participants", params={"email": "not@there.com"})
    assert response.status_code == 404


def test_unregister_activity_not_found_returns_404(client):
    response = client.delete("/activities/NoSuchActivity/participants", params={"email": "a@b.com"})
    assert response.status_code == 404
