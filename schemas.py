from pydantic import *
from enum import Enum

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