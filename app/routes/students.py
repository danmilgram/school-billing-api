from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate
from app.schemas.account_statement import StudentAccountStatement
from app.services.student_service import StudentService
from app.services.account_statement_service import AccountStatementService

router = APIRouter(prefix="/students", tags=["students"])


@router.post("/", response_model=StudentRead, status_code=201)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    """Create a new student"""
    return StudentService.create(student, db)


@router.get("/", response_model=List[StudentRead])
def list_students(db: Session = Depends(get_db)):
    """List all students (excluding soft-deleted)"""
    return StudentService.get_all(db)


@router.get("/{student_id}", response_model=StudentRead)
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Get a student by ID"""
    student = StudentService.get_by_id(student_id, db)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.put("/{student_id}", response_model=StudentRead)
def update_student(student_id: int, student_update: StudentUpdate, db: Session = Depends(get_db)):
    """Update a student"""
    student = StudentService.get_by_id(student_id, db)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return StudentService.update(student, student_update, db)


@router.delete("/{student_id}", status_code=204)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """Soft delete a student"""
    student = StudentService.get_by_id(student_id, db)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    StudentService.delete(student, db)
    return None


@router.get("/{student_id}/account-statement", response_model=StudentAccountStatement)
def get_student_account_statement(student_id: int, db: Session = Depends(get_db)):
    """Get account statement for a student"""
    statement = AccountStatementService.get_student_statement(student_id, db)
    if not statement:
        raise HTTPException(status_code=404, detail="Student not found")
    return statement
