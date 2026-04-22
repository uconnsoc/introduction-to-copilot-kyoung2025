import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Reset activities to a clean state before each test.
    This ensures test isolation and prevents tests from affecting each other.
    """
    # Save original state
    original_activities = dict(activities)
    
    # Reset to minimal test data
    activities.clear()
    activities.update({
        "Test Activity A": {
            "description": "Test activity for unit tests",
            "schedule": "Mondays, 3:00 PM - 4:00 PM",
            "max_participants": 5,
            "participants": []
        },
        "Test Activity B": {
            "description": "Another test activity",
            "schedule": "Wednesdays, 3:00 PM - 4:00 PM",
            "max_participants": 3,
            "participants": ["existing@test.edu"]
        }
    })
    
    yield
    
    # Restore original state after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self):
        """
        Arrange: Initialize TestClient
        Act: Make GET request to /activities
        Assert: Verify status code 200 and response contains activities
        """
        # Arrange
        client = TestClient(app)
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Test Activity A" in data
        assert "Test Activity B" in data
    
    def test_get_activities_has_correct_structure(self):
        """
        Arrange: Initialize TestClient
        Act: Make GET request to /activities
        Assert: Verify each activity has required fields
        """
        # Arrange
        client = TestClient(app)
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful_new_participant(self):
        """
        Arrange: Initialize TestClient with known activity
        Act: Sign up a new student for the activity
        Assert: Verify status 200 and participant is added
        """
        # Arrange
        client = TestClient(app)
        email = "newstudent@test.edu"
        activity_name = "Test Activity A"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    
    def test_signup_prevents_duplicate_registration(self):
        """
        Arrange: Student already registered for an activity
        Act: Attempt to sign up the same student again
        Assert: Verify status 400 and appropriate error message
        """
        # Arrange
        client = TestClient(app)
        email = "existing@test.edu"
        activity_name = "Test Activity B"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_fails_for_nonexistent_activity(self):
        """
        Arrange: Initialize TestClient with invalid activity name
        Act: Attempt to sign up for non-existent activity
        Assert: Verify status 404 and error message
        """
        # Arrange
        client = TestClient(app)
        email = "student@test.edu"
        activity_name = "Nonexistent Activity"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_removes_participant(self):
        """
        Arrange: Student registered for an activity
        Act: Unregister the student
        Assert: Verify status 200 and participant is removed
        """
        # Arrange
        client = TestClient(app)
        email = "existing@test.edu"
        activity_name = "Test Activity B"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email not in activities[activity_name]["participants"]
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    
    def test_unregister_fails_for_nonexistent_activity(self):
        """
        Arrange: Initialize TestClient with invalid activity
        Act: Attempt to unregister from non-existent activity
        Assert: Verify status 404 and error message
        """
        # Arrange
        client = TestClient(app)
        email = "student@test.edu"
        activity_name = "Nonexistent Activity"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_fails_if_not_registered(self):
        """
        Arrange: Student NOT registered for an activity
        Act: Attempt to unregister the student
        Assert: Verify status 400 and appropriate error message
        """
        # Arrange
        client = TestClient(app)
        email = "notregistered@test.edu"
        activity_name = "Test Activity B"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]


class TestRootRedirect:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static_index(self):
        """
        Arrange: Initialize TestClient
        Act: Make GET request to root path
        Assert: Verify redirect status and location header
        """
        # Arrange
        client = TestClient(app)
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
