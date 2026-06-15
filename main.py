from fastapi import FastAPI, HTTPException
from typing import Optional
from models import Employee, EmployeeCreate

app = FastAPI()

db: list[Employee] = [
    Employee(id=1, name="Alice",   department="Engineering", salary=90000),
    Employee(id=2, name="Bob",     department="Marketing",   salary=75000),
    Employee(id=3, name="Charlie", department="Engineering", salary=85000),
]
next_id = 4


def find(emp_id: int):
    return next((e for e in db if e.id == emp_id), None)

  
@app.get("/employees")
def get_employees(department: Optional[str] = None):
    if department:
        return [e for e in db if e.department.lower() == department.lower()]
    return db


@app.get("/employees/{emp_id}")
def get_employee(emp_id: int):
    emp = find(emp_id)
    if not emp:
        raise HTTPException(404, "Employee not found")
    return emp


@app.post("/employees", status_code=201)
def create_employee(data: EmployeeCreate):
    global next_id
    emp = Employee(id=next_id, **data.model_dump())
    db.append(emp)
    next_id += 1
    return emp


@app.put("/employees/{emp_id}")
def update_employee(emp_id: int, data: EmployeeCreate):
    emp = find(emp_id)
    if not emp:
        raise HTTPException(404, "Employee not found")
    db[db.index(emp)] = Employee(id=emp_id, **data.model_dump())
    return db[db.index(find(emp_id))]


@app.delete("/employees/{emp_id}", status_code=204)
def delete_employee(emp_id: int):
    emp = find(emp_id)
    if not emp:
        raise HTTPException(404, "Employee not found")
    db.remove(emp)
