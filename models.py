from pydantic import BaseModel

class Employee(BaseModel):
    id: int
    name: str
    department: str
    salary: float


class EmployeeCreate(BaseModel):
    name: str
    department: str
    salary: float
