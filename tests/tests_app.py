import pytest
import json
from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# 1 GET/tasks 
def test_get_tasks(client):
    # HTTP reuest check 
    response = client.get("/tasks")
    assert response.status_code == 200
    # Data integrity check. Endpoint ought not to return unexpected datatypes rather than list; this provides API consistency.
    # Also checks if the "load_tasks" function returns expected data.
    data = response.get_json()
    assert isinstance(data, list)

# 2 POST /tasks
def test_add_task(client):
    response = client.post("/tasks", json={"title": "Writing Pytest tests", "category": "Programming"})
    assert response.status_code == 201
    assert response.json["title"] == "Writing Pytest tests"
    assert response.json["category"] == "Programming"
    assert response.json["completed"] is False

# 3 GET /tasks/{task_id}
def test_get_task_id(client):
    # add a task first, and then, test it.
    response = client.post("/tasks", json={"description": "Writing Pytest tests", "category": "Programming"})
    task_id = response.get_json()["id"]

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["description"] == "Writing Pytest tests"
    assert data["category"] == "Programming"

# 4 PUT /tasks/{task_id}
def test_update_task(client):
    # Add a task first
    response = client.post("/tasks", json={"description": "Pytest tests", "category": "Programming"})
    task_id = response.get_json()["id"]

    # Then update it
    updated_data = {
        "description": "Updated Pytest tests",
        "category": "Programming",
        "status": "completed"
    }
    # Test HTTP request
    response = client.put(f"/tasks/{task_id}", json=updated_data)
    assert response.status_code == 200
    # Test data
    data = response.get_json()
    assert data["description"] == "Updated Pytest tests"
    assert data["category"] == "Programming"
    assert data["status"] == "completed"

# 5 PUT /tasks/{task_id}/complete
def test_mark_task_complete(client):
    response = client.post("/tasks", json={"title": "Writing Pytest tests", "category": "Programming"})
    task_id = response.json["id"]

    response = client.put(f"/tasks/{task_id}/complete")
    assert response.status_code == 200

    assert response.json["completed"] is True

# 6 DELETE /tasks/{task_id}
def test_delete_task(client):
    response = client.post("/tasks", json={"description": "Deleting Pytest tests", "category": "Programming"})
    task_id = response.get_json()["id"]

    response = client.delete(f"/tasks/{task_id}", json={"password": "123"})
    assert response.status_code == 200

    data = response.get_json()
    assert "eternally deleted" in data["message"]

# 7 GET /tasks/categories/
def test_get_categories(client):
    response = client.get("/tasks/categories")
    assert response.status_code == 200
    # Data integrity
    data = response.get_json()
    assert isinstance(data["categories"], list)

# 8 GET /tasks/categories/{category_name}
def test_get_tasks_by_category(client):
    client.post("/tasks", json={"description": "Pytest category", "category": "Programming"})

    response = client.get("/tasks/categories/Programming")
    assert response.status_code == 200
    # Data integrity
    data = response.get_json()
    assert isinstance(data, list)
    assert data[0]["category"] == "Programming"

# 9 Frontend GET("/")
def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Task List" in response.data

# 10 Add new task via frontend POST ("/submit")
def test_submit_task(client):
    response = client.post("/submit", data={
        "description": "Submitted task",
        "category": "Submitting"
    })
    assert response.status_code == 302 # HTTP 302 Found redirection response status code to the homepage
    assert b"Task List" in client.get("/").data
