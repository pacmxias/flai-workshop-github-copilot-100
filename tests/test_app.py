"""
Tests for the Mergington High School API (FastAPI)
"""

import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the activities dict to its original state after each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


client = TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self):
        response = client.get("/activities")
        assert response.status_code == 200

    def test_returns_all_activities(self):
        response = client.get("/activities")
        data = response.json()
        assert len(data) == 9

    def test_activity_has_required_fields(self):
        response = client.get("/activities")
        data = response.json()
        for activity in data.values():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity

    def test_known_activity_present(self):
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data

    def test_participants_is_list(self):
        response = client.get("/activities")
        data = response.json()
        for activity in data.values():
            assert isinstance(activity["participants"], list)


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_signup_success(self):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]

    def test_signup_success_response_message(self):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_activity_not_found(self):
        response = client.post(
            "/activities/Underwater Basket Weaving/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_already_registered(self):
        # lucas is already in Soccer Team
        response = client.post(
            "/activities/Soccer Team/signup",
            params={"email": "lucas@mergington.edu"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is already signed up for this activity"

    def test_signup_adds_to_participants_list(self):
        email = "newstudent@mergington.edu"
        before = len(activities["Art Club"]["participants"])
        client.post("/activities/Art Club/signup", params={"email": email})
        assert len(activities["Art Club"]["participants"]) == before + 1

    def test_signup_different_students_same_activity(self):
        client.post("/activities/Chess Club/signup", params={"email": "student1@mergington.edu"})
        client.post("/activities/Chess Club/signup", params={"email": "student2@mergington.edu"})
        participants = activities["Chess Club"]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/unregister
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_unregister_success(self):
        response = client.delete(
            "/activities/Soccer Team/unregister",
            params={"email": "lucas@mergington.edu"},
        )
        assert response.status_code == 200
        assert "lucas@mergington.edu" not in activities["Soccer Team"]["participants"]

    def test_unregister_success_response_message(self):
        response = client.delete(
            "/activities/Soccer Team/unregister",
            params={"email": "lucas@mergington.edu"},
        )
        data = response.json()
        assert "message" in data
        assert "lucas@mergington.edu" in data["message"]

    def test_unregister_activity_not_found(self):
        response = client.delete(
            "/activities/Underwater Basket Weaving/unregister",
            params={"email": "anyone@mergington.edu"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_student_not_registered(self):
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "notregistered@mergington.edu"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not signed up for this activity"

    def test_unregister_removes_from_participants_list(self):
        email = "ethan@mergington.edu"
        assert email in activities["Soccer Team"]["participants"]
        client.delete("/activities/Soccer Team/unregister", params={"email": email})
        assert email not in activities["Soccer Team"]["participants"]

    def test_signup_then_unregister_roundtrip(self):
        email = "roundtrip@mergington.edu"
        client.post("/activities/Drama Club/signup", params={"email": email})
        assert email in activities["Drama Club"]["participants"]

        client.delete("/activities/Drama Club/unregister", params={"email": email})
        assert email not in activities["Drama Club"]["participants"]


# ---------------------------------------------------------------------------
# GET / (redirect)
# ---------------------------------------------------------------------------

class TestRoot:
    def test_root_redirects(self):
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (301, 302, 307, 308)
        assert "/static/index.html" in response.headers["location"]
