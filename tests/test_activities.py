"""Unit tests for FastAPI activity management endpoints

This test module uses the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and fixtures
- Act: Execute the code being tested
- Assert: Verify the results
"""
import pytest


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that GET / redirects to /static/index.html
        
        AAA Pattern:
        - Arrange: Client is provided by fixture
        - Act: Make GET request to root endpoint without following redirects
        - Assert: Verify redirect status code and location header
        """
        # Arrange
        # (client fixture is already set up)
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""
    
    def test_get_all_activities(self, client):
        """Test that GET /activities returns all activities with correct structure
        
        AAA Pattern:
        - Arrange: Client is provided by fixture
        - Act: Request all activities from endpoint
        - Assert: Verify response status, data type, and activity structure
        """
        # Arrange
        # (client fixture is already set up)
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Verify structure of an activity
        activity = next(iter(data.values()))
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
    
    def test_get_activities_contains_chess_club(self, client):
        """Test that Chess Club activity is returned with valid structure
        
        AAA Pattern:
        - Arrange: Client is provided by fixture
        - Act: Request all activities from endpoint
        - Assert: Verify Chess Club is present with expected fields
        """
        # Arrange
        # (client fixture is already set up)
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert "Chess Club" in data
        assert data["Chess Club"]["description"] is not None
        assert isinstance(data["Chess Club"]["participants"], list)
    
    def test_get_activities_contains_programming_class(self, client):
        """Test that Programming Class activity is returned
        
        AAA Pattern:
        - Arrange: Client is provided by fixture
        - Act: Request all activities from endpoint
        - Assert: Verify Programming Class exists with participants
        """
        # Arrange
        # (client fixture is already set up)
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert "Programming Class" in data
        assert len(data["Programming Class"]["participants"]) > 0


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client, sample_activity, sample_email):
        """Test successful student signup for an activity"""
        response = client.post(
            f"/activities/{sample_activity}/signup",
            params={"email": sample_email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert sample_email in data["message"]
        assert sample_activity in data["message"]
    
    def test_signup_updates_participants_list(self, client, sample_activity):
        """Test that signup actually adds the student to participants"""
        email = "newstudent@mergington.edu"
        
        # Get initial count
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[sample_activity]["participants"].copy()
        initial_count = len(initial_participants)
        
        # Sign up new student
        signup_response = client.post(
            f"/activities/{sample_activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify student was added
        after_response = client.get("/activities")
        after_participants = after_response.json()[sample_activity]["participants"]
        assert len(after_participants) == initial_count + 1
        assert email in after_participants
    
    def test_signup_multiple_students(self, client, sample_activity):
        """Test signing up multiple different students"""
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(
                f"/activities/{sample_activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful(self, client, sample_activity):
        """Test successful student unregistration from an activity"""
        # First, get an existing participant to unregister
        activities_response = client.get("/activities")
        participants = activities_response.json()[sample_activity]["participants"]
        email_to_unregister = participants[0]
        
        response = client.delete(
            f"/activities/{sample_activity}/unregister",
            params={"email": email_to_unregister}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email_to_unregister in data["message"]
        assert sample_activity in data["message"]
    
    def test_unregister_removes_from_participants(self, client, sample_activity):
        """Test that unregister actually removes the student from participants"""
        # First, sign up a student
        email = "unregister_test@mergington.edu"
        client.post(
            f"/activities/{sample_activity}/signup",
            params={"email": email}
        )
        
        # Verify signup was successful
        before_unregister = client.get("/activities")
        assert email in before_unregister.json()[sample_activity]["participants"]
        
        # Now unregister
        unregister_response = client.delete(
            f"/activities/{sample_activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify student was removed
        after_unregister = client.get("/activities")
        assert email not in after_unregister.json()[sample_activity]["participants"]
    
    def test_unregister_multiple_students(self, client, sample_activity):
        """Test unregistering multiple students"""
        emails = [
            "unreg1@mergington.edu",
            "unreg2@mergington.edu"
        ]
        
        # Sign up students first
        for email in emails:
            client.post(
                f"/activities/{sample_activity}/signup",
                params={"email": email}
            )
        
        # Unregister each student
        for email in emails:
            response = client.delete(
                f"/activities/{sample_activity}/unregister",
                params={"email": email}
            )
            assert response.status_code == 200


class TestEndpointIntegration:
    """Integration tests combining multiple endpoints"""
    
    def test_signup_and_unregister_workflow(self, client, sample_activity):
        """Test complete workflow: signup then unregister"""
        email = "workflow_test@mergington.edu"
        
        # Step 1: Sign up
        signup_response = client.post(
            f"/activities/{sample_activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Step 2: Verify signup in activities list
        activities_response = client.get("/activities")
        assert email in activities_response.json()[sample_activity]["participants"]
        
        # Step 3: Unregister
        unregister_response = client.delete(
            f"/activities/{sample_activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Step 4: Verify removal from activities list
        final_activities = client.get("/activities")
        assert email not in final_activities.json()[sample_activity]["participants"]
