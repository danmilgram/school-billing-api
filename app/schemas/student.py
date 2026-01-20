from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.student import StudentStatus


class StudentBase(BaseModel):
    school_id: int
    first_name: str
    last_name: str
    email: EmailStr
    enrollment_date: date
    status: StudentStatus = StudentStatus.ACTIVE


class StudentCreate(StudentBase):
    pass


class StudentUpdate(StudentBase):
    school_id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    enrollment_date: Optional[date] = None
    status: Optional[StudentStatus] = None


class StudentRead(StudentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
