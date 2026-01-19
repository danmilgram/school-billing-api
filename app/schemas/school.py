from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SchoolBase(BaseModel):
    name: str
    contact_email: str
    contact_phone: str


class SchoolCreate(SchoolBase):
    pass


class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class SchoolRead(SchoolBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
