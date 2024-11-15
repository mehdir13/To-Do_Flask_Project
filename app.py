from flask import Flask, jsonify, request, render_template, redirect, url_for
from functools import wraps
import json
import os

app = Flask(__name__)

app.config['TEMPLATES_AUTO_RELOAD'] = True

# We use the JSON file as our primitive database (single user access only - not gonna work for multiple users);
# therefore we need functions to read & write data from and into the database:
# All endpoint functions follow the same algorithm: load data from json file, check if the ID exists, validate user inputs, manipulate data, re-write the json file.

# Database function (i): reads the current tasks from the tasks.json file
def load_tasks():
    if os.path.exists("tasks.json"):
        with open("tasks.json", "r") as file:
            print("JSON successfully loaded")
            return json.load(file)
    print("tasks.json file not found")
    return[]


# Database function (ii): writes updated tasks back to the tasks.json file whenever tasks are added, updated, or deleted.
def save_tasks(tasks):
    with open("tasks.json", "w") as file:
        json.dump(tasks, file, indent=4)

# Task ID generator. (ALSO handles an empty tasks list:)
def generate_new_id(tasks):
    if not tasks:
        return 1
    return max(task["id"] for task in tasks) + 1

# Authorization decorator
def require_authorization(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        data = request.get_json()
        
        # 'data' cannnot be empty nor anything other than a dictionary
        if data is None or not isinstance(data, dict):
            return jsonify({"error": "Invalid request body, expecting JSON"}), 400
        
        # Password check
        if data.get("password") != "123":
            return jsonify({"error": "Unauthorized"}), 403
    
        return func(*args, **kwargs)
    return wrapper


# GET/tasks: gets all tasks. Add a parameter "completed" which can filter on completed or uncompleted tasks.
@app.route("/tasks", methods=["GET"])
def get_tasks():
    tasks = load_tasks()
    completed = request.args.get("completed")

    if completed is not None:
        if completed.lower() == "true":
            tasks = [task for task in tasks if task["status"] == "completed"]
        elif completed.lower() == "false":
            tasks = [task for task in tasks if task["status"] == "pending"]
    
    return jsonify(tasks), 200

# POST /tasks: adds a new task. The task is uncompleted (= 'pending') when it is first added.
@app.route("/tasks", methods=["POST"])
def add_task():
    # Validation 1: JSON file parsing
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON format"}), 400
    except Exception as e:
        return jsonify({"error": "Failed to parse JSON", "details": str(e)}), 400

    # Validation 2: user input - check if description ot category not empty
    required_fields = ["description", "category"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    # Validation 3: user input - data types of the fields should be only STRING
    if not isinstance(data["description"], str) or not isinstance(data["category"], str):
        return jsonify({"error": "Fields 'description' and 'category' must be strings"}), 400

    tasks = load_tasks()
    new_id = generate_new_id(tasks)
    new_task = {
        "id": new_id,
        "description": data["description"],
        "category": data["category"],
        "status": "pending"
    }
    tasks.append(new_task)

    save_tasks(tasks)
    return jsonify(new_task), 201

# GET /tasks/{task_id} : gets a task with a specific id
@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    tasks = load_tasks()
    print(f"Loaded tasks: {tasks}")  # Debug ("ID 123 not found" !!!): Print loaded tasks to check the JSON not corrupt
    task = next((task for task in tasks if task["id"] == task_id), None)
    if task is None:
        return jsonify({"error": f"Task with ID {task_id} not found"}), 404
    return jsonify(task), 200

# PUT /tasks/{task_id} : updates a task by ID
@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    tasks = load_tasks()
    task = next((task for task in tasks if task["id"] == task_id), None)
    # JSON not corrupt, not empty, task exists in tasks.json
    if task is None:
        return jsonify({"error": f"Task with ID {task_id} not found"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400

    # User input validation: data type should be STRING. Status can only be either completed or pending: excluded middle.
    if "description" in data:
        if not isinstance(data["description"], str):
            return jsonify({"error": "Field 'description' must be a string"}), 400
        task["description"] = data["description"]

    if "category" in data:
        if not isinstance(data["category"], str):
            return jsonify({"error": "Field 'category' must be a string"}), 400
        task["category"] = data["category"]

    if "status" in data:
        if data["status"] not in ["pending", "completed"]:
            return jsonify({"error": "Field's 'status' must be either 'pending' or 'completed'"}), 400
        task["status"] = data["status"]

    save_tasks(tasks)
    return jsonify(task), 200

# PUT /tasks/{task_id}/complete : marks a task as completed
@app.route("/tasks/<int:task_id>/complete", methods=["PUT"])
def mark_task_complete(task_id):
    tasks = load_tasks()
    task = next((task for task in tasks if task["id"] == task_id), None)
    if task is None:
        return jsonify({"error": f"Task with ID {task_id} not found"}), 404
    task["status"] = "completed"

    save_tasks(tasks)
    return jsonify(task), 200

# DELETE /tasks/{task_id} : deletes a task by ID with authorization
@app.route("/tasks/<int:task_id>", methods=["DELETE"])
@require_authorization
def delete_task(task_id):
    tasks = load_tasks()
    task = next((task for task in tasks if task["id"] == task_id), None)
    if task is None:
        return jsonify({"error": f"Task with ID {task_id} not found"}), 404
    tasks.remove(task)

    save_tasks(tasks)
    return jsonify({"message": f"Task '{task['description']}' with ID {task_id} was eternally deleted from your chores"}), 200

# GET /tasks/categories/ : gets all different categories
@app.route("/tasks/categories", methods=["GET"])
def get_categories():
    tasks = load_tasks()
    categories = list(set(task["category"] for task in tasks if "category" in task))

    return jsonify({"categories": categories}), 200

# GET /tasks/categories/{category_name} : gets all tasks from a specific category.
@app.route("/tasks/categories/<category_name>", methods=["GET"])
def get_tasks_by_category(category_name):
    tasks = load_tasks()
    filtered_tasks = [
        task for task in tasks 
        if isinstance(task, dict) and task.get("category") == category_name
    ]
    if not filtered_tasks:
        return jsonify({"error": f"No tasks found in category '{category_name}'"}), 404
    return jsonify(filtered_tasks), 200

# RAW tets for debugging - delete in final version
@app.route("/tasks_raw")
def tasks_raw():
    tasks = load_tasks()
    return {"tasks": tasks}


# Frontend route to view tasks
# HTML page has not been loading in the browser; probably the keyboard was not on ENG while typing the "templaes" name:
# SET THE KEYBOARDS LANGUAGE ON BLODDY ENGLISH while writing code !!!!
@app.route("/", methods=["GET"])
def index():
    tasks = load_tasks()
    if not tasks:
        return "Hurray! NO tasks to do!", 404

    return render_template("index.html", tasks=tasks)

@app.route("/submit", methods=["GET", "POST"])
def submit_task():
    if request.method == "POST":
        description = request.form.get("description")
        category = request.form.get("category")

        if description and category:
            tasks = load_tasks()
            new_task = {
                "id": generate_new_id(tasks),
                "description": description,
                "category": category,
                "status": "pending"
            }
            tasks.append(new_task)
            save_tasks(tasks)
            return redirect(url_for("index"))

    return render_template("submit.html")

if __name__ == "__main__":
    app.run(debug=True)