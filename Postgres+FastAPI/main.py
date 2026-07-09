from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db, engine
import models
import schemas

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/employees",response_model=list[schemas.EmployeeOut])
def get_all(db:Session=Depends(get_db)):
    return db.query(models.Employee).all()

@app.get("/employees/department/{dept_name}",response_model=list[schemas.EmployeeOut])
def get_by_dept(dept_name:str,db:Session=Depends(get_db),skip:int=0,limit:int=5):
    emps = ( db.query(models.Employee).filter(models.Employee.department==dept_name).offset(skip).limit(limit).all())
    if not emps:
        raise HTTPException(404, f"No employees found in the department")
    return emps

@app.get("/employees/{emp_id}",response_model = schemas.EmployeeOut)
def get_employee(emp_id:int, db:Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(404,"Employee not found")
    return emp

@app.post("/employees/create",response_model=schemas.EmployeeOut,status_code=201)
def create_employee(data:schemas.EmployeeCreate,db:Session=Depends(get_db)):
    emp = models.Employee(**data.model_dump())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp 

@app.put("/employees/modify/{emp_id}",response_model=schemas.EmployeeOut)
def update_emp(emp_id:int,data:schemas.EmployeeCreate,db:Session=Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(404,"Employee not found")
    for key,value in data.model_dump().items():
        setattr(emp,key,value)
    db.commit()
    db.refresh(emp)
    return emp

@app.delete("/employee/delete/{emp_id}",status_code=204)
def delete_employee(emp_id:int,db:Session=Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employees.id == emp_id).first()
    if not emp:
        raise HTTPException(404, "employee not Found")
    db.delete(emp)
    db.commit()
