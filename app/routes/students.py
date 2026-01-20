from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate
from app.schemas.account_statement import StudentAccountStatement
from app.services.student_service import StudentService
from app.services.account_statement_service import AccountStatementService

router = APIRouter(prefix="/students", tags=["students"])


@router.post("/", response_model=StudentRead, status_code=201)
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new student (requires admin role)"""
    return StudentService.create(student, db)


@router.get("/", response_model=List[StudentRead])
def list_students(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all students (excluding soft-deleted) with pagination (requires authentication)"""
    return StudentService.get_all(db, skip=skip, limit=limit)


@router.get("/{student_id}", response_model=StudentRead)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a student by ID (requires authentication)"""
    student = StudentService.get_by_id(student_id, db)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.put("/{student_id}", response_model=StudentRead)
def update_student(
    student_id: int,
    student_update: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a student (requires admin role)"""
    student = StudentService.get_by_id(student_id, db)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return StudentService.update(student, student_update, db)


@router.delete("/{student_id}", status_code=204)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Soft delete a student (requires admin role)"""
    student = StudentService.get_by_id(student_id, db)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    StudentService.delete(student, db)
    return None


@router.get("/{student_id}/account-statement", response_model=StudentAccountStatement, response_model_exclude_none=True)
def get_student_account_statement(
    student_id: int,
    start_date: date = Query(..., description="Filter invoices issued on or after this date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Filter invoices issued on or before this date (YYYY-MM-DD)"),
    include_invoices: bool = Query(False, description="Whether to include the list of invoices in the response"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get account statement for a student with date range filtering (requires admin role)

    Query parameters:
    - start_date (required): Filter for invoices issued on or after this date (format: YYYY-MM-DD)
    - end_date (required): Filter for invoices issued on or before this date (format: YYYY-MM-DD)
    - include_invoices (optional, default: false): Include the list of invoices in the response
    """
    statement = AccountStatementService.get_student_statement(
        student_id, db, start_date=start_date, end_date=end_date, include_invoices=include_invoices
    )
    if not statement:
        raise HTTPException(status_code=404, detail="Student not found")
    return statement
