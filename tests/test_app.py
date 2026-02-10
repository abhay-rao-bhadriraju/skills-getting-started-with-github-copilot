"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    original_activities = {
        "Basketball Team": {
            "description": "Competitive basketball team for intramural and regional tournaments",
            "schedule": "Mondays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["marcus@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Learn tennis skills and participate in friendly matches",
            "schedule": "Wednesdays and Saturdays, 3:00 PM - 4:30 PM",
            "max_participants": 16,
            "participants": ["alex@mergington.edu"]
        },
        "Drama Club": {
            "description": "Perform in theatrical productions and improve acting skills",
            "schedule": "Tuesdays and Fridays, 4:00 PM - 5:30 PM",
            "max_participants": 25,
            "participants": ["jessica@mergington.edu", "james@mergington.edu"]
        },
    }
    
    # Clear current activities
    activities.clear()
    # Add back original activities
    activities.update(original_activities)
    
    yield
    
    # Cleanup
    activities.clear()
    activities.update(original_activities)


def test_root_redirect(client):
    """Test that root endpoint redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client, reset_activities):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    data = response.json()
    assert "Basketball Team" in data
    assert "Tennis Club" in data
    assert "Drama Club" in data
    
    # Verify activity structure
    basketball = data["Basketball Team"]
    assert basketball["description"] == "Competitive basketball team for intramural and regional tournaments"
    assert basketball["max_participants"] == 15
    assert "marcus@mergington.edu" in basketball["participants"]


def test_signup_for_activity(client, reset_activities):
    """Test signing up for an activity"""
    response = client.post("/activities/Basketball%20Team/signup?email=newstudent@mergington.edu")
    assert response.status_code == 200
    
    data = response.json()
    assert "Signed up newstudent@mergington.edu for Basketball Team" in data["message"]
    
    # Verify participant was added
    assert "newstudent@mergington.edu" in activities["Basketball Team"]["participants"]


def test_signup_duplicate_participant(client, reset_activities):
    """Test that signing up twice raises an error"""
    # First signup
    response1 = client.post("/activities/Basketball%20Team/signup?email=duplicate@mergington.edu")
    assert response1.status_code == 200
    
    # Second signup with same email
    response2 = client.post("/activities/Basketball%20Team/signup?email=duplicate@mergington.edu")
    assert response2.status_code == 400
    
    data = response2.json()
    assert "already signed up" in data["detail"]


def test_signup_activity_not_found(client, reset_activities):
    """Test signing up for non-existent activity"""
    response = client.post("/activities/NonExistent/signup?email=student@mergington.edu")
    assert response.status_code == 404
    
    data = response.json()
    assert "Activity not found" in data["detail"]


def test_remove_participant(client, reset_activities):
    """Test removing a participant from an activity"""
    # First add a participant
    client.post("/activities/Basketball%20Team/signup?email=newstudent@mergington.edu")
    
    # Then remove them
    response = client.delete("/activities/Basketball%20Team/participants/newstudent%40mergington.edu")
    assert response.status_code == 200
    
    data = response.json()
    assert "Removed newstudent@mergington.edu from Basketball Team" in data["message"]
    
    # Verify participant was removed
    assert "newstudent@mergington.edu" not in activities["Basketball Team"]["participants"]


def test_remove_nonexistent_participant(client, reset_activities):
    """Test removing a participant that doesn't exist"""
    response = client.delete("/activities/Basketball%20Team/participants/nonexistent%40mergington.edu")
    assert response.status_code == 404
    
    data = response.json()
    assert "Participant not found" in data["detail"]


def test_remove_from_nonexistent_activity(client, reset_activities):
    """Test removing a participant from non-existent activity"""
    response = client.delete("/activities/NonExistent/participants/student%40mergington.edu")
    assert response.status_code == 404
    
    data = response.json()
    assert "Activity not found" in data["detail"]


def test_participants_count_accuracy(client, reset_activities):
    """Test that participant counts are accurate"""
    # Get initial count
    response = client.get("/activities")
    basketball = response.json()["Basketball Team"]
    initial_count = len(basketball["participants"])
    
    # Add participant
    client.post("/activities/Basketball%20Team/signup?email=test1@mergington.edu")
    response = client.get("/activities")
    basketball = response.json()["Basketball Team"]
    assert len(basketball["participants"]) == initial_count + 1
    
    # Remove participant
    client.delete("/activities/Basketball%20Team/participants/test1%40mergington.edu")
    response = client.get("/activities")
    basketball = response.json()["Basketball Team"]
    assert len(basketball["participants"]) == initial_count
