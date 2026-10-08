from fastapi import FastAPI

app = FastAPI() 
employees = [{"id": 1, "name": "John Doe", "position": "Manager"},
             {"id": 2, "name": "Jane Smith", "position": "Developer"},
             {"id": 3, "name": "Alice Johnson", "position": "Designer"},
             {"id": 4, "name": "Bob Brown", "position": "Tester"}]

@app.get("/employees")
def get_employees():
    return {"employees": employees}

@app.get("/employees/{employee_id}")
def get_employee(employee_id: int):
    for employee in employees:
        if employee["id"] == employee_id:
            return {"employee": employee}
    return {"error": "Employee not found"}

@app.get("/employees/name/{employee_name}")
def get_employee_by_name(employee_name: str):
    for employee in employees:
        if employee["name"].lower() == employee_name.lower():
            return {"employee": employee}
    return {"error": "Employee not found"}