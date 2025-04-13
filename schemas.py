from pydantic import *
from enum import Enum
from datetime import datetime
from uuid import UUID
import uuid  




class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "employee"



class UserTypeRequest(BaseModel):
    role: str


class CityEnum(str, Enum):
    moscow = "Москва"
    spb = "Санкт-Петербург"
    kazan = "Казань"

class PVZCreate(BaseModel):
    city: CityEnum




class ReceptionCreate(BaseModel):
    pvzId: UUID

class Reception(BaseModel):
    id: UUID
    pvzid: UUID
    datetime: datetime  
    status: str  



class Error(BaseModel):
    detail: str
