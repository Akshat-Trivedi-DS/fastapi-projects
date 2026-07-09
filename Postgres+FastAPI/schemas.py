from pydantic import BaseModel


class EmployeeCreate(BaseModel):
    name:str
    department:str
    salary:float



class EmployeeOut(BaseModel):
    id : int
    name : str
    department: str
    salary : float 

    class Config:
        from_attributes = True