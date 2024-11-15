import pytest
import json
from app import app, load_tasks, save_tasks, generate_new_id


# Test Client: a tool provided by Flask that allows you to test your Flask application without actually running the server.
# It simulates HTTP requests to your routes.
    
@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["DEBUG"] = True
    with app.test_client() as client:
        yield client

def setup_module(module):
    # Prepare a sample tasks.json for testing
    with open("tasks.json", "w") as f:
        json.dump([], f, indent=4)


# GET /tasks
def test_get_tasks(client):
    response = client.get("/tasks")
    assert response.status_code == 200
    assert isinstance(response.json, list)

# POST /tasks
def test_add_task(client):
    task_data = {
        "description": "Write unit tests",
        "category": "Development"
    }
    response = client.post("/tasks", json=task_data)
    assert response.status_code == 201
    assert response.json["description"] == "Write unit tests"
    assert response.json["status"] == "pending"

# GET /tasks/{task_id}
def test_get_task_by_id(client):
    # Add a specific task first
    task_data = {
        "description": "Review code",
        "category": "Development"
    }
    post_response = client.post("/tasks", json=task_data)
    assert post_response.status_code == 201
    task_id = post_response.json["id"]

    # Now, fetch the task by its ID
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json["description"] == "Review code"

# PUT /tasks/{task_id}
def test_update_task(client):
    task_data = {
        "description": "Fix bugs",
        "category": "Development"
    }
    client.post("/tasks", json=task_data)
    updated_data = {
        "description": "Fix critical bugs",
        "status": "completed"
    }
    response = client.put("/tasks/1", json=updated_data)
    assert response.status_code == 200
    assert response.json["description"] == "Fix critical bugs"
    assert response.json["status"] == "completed"

# PUT /tasks/{task_id}/complete
def test_mark_task_complete(client):
    task_data = {
        "description": "Refactor code",
        "category": "Development"
    }
    client.post("/tasks", json=task_data)
    response = client.put("/tasks/1/complete")
    assert response.status_code == 200
    assert response.json["status"] == "completed"

# DELETE /tasks/{task_id}
def test_delete_task(client):
    task_data = {
        "description": "Prepare report",
        "category": "Work"
    }
    client.post("/tasks", json=task_data)
    response = client.delete("/tasks/1", json={"password": "123"})
    assert response.status_code == 200
    assert "deleted" in response.json["message"]

# GET /tasks/categories
def test_get_categories(client):
    response = client.get("/tasks/categories")
    assert response.status_code == 200
    assert isinstance(response.json["categories"], list)

# GET /tasks/categories/{category_name}
def test_get_tasks_by_category(client):
    task_data = {
        "description": "Learn Flask",
        "category": "Education"
    }
    client.post("/tasks", json=task_data)
    response = client.get("/tasks/categories/Education")
    assert response.status_code == 200
    assert len(response.json) > 0

# Authorization
def test_delete_task_unauthorized(client):
    task_data = {
        "description": "Secure endpoint",
        "category": "Security"
    }
    client.post("/tasks", json=task_data)
    response = client.delete("/tasks/1", json={"password": "wrong"})
    assert response.status_code == 403
    assert response.json["error"] == "Unauthorized"