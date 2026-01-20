from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.school import SchoolCreate, SchoolRead, SchoolUpdate
from app.schemas.account_statement import SchoolAccountStatement
from app.services.school_service import SchoolService
from app.services.account_statement_service import AccountStatementService

router = APIRouter(prefix="/schools", tags=["schools"])


@router.post("/", response_model=SchoolRead, status_code=201)
def create_school(
    school: SchoolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new school (requires admin role)"""
    return SchoolService.create(school, db)


@router.get("/", response_model=List[SchoolRead])
def list_schools(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all schools (excluding soft-deleted) with pagination (requires authentication)"""
    return SchoolService.get_all(db, skip=skip, limit=limit)


@router.get("/{school_id}", response_model=SchoolRead)
def get_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a school by ID (requires authentication)"""
    school = SchoolService.get_by_id(school_id, db)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school


@router.put("/{school_id}", response_model=SchoolRead)
def update_school(
    school_id: int,
    school_update: SchoolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a school (requires admin role)"""
    school = SchoolService.get_by_id(school_id, db)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return SchoolService.update(school, school_update, db)


@router.delete("/{school_id}", status_code=204)
def delete_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Soft delete a school (requires admin role)"""
    school = SchoolService.get_by_id(school_id, db)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    SchoolService.delete(school, db)
    return None


@router.get("/{school_id}/account-statement", response_model=SchoolAccountStatement, response_model_exclude_none=True)
def get_school_account_statement(
    school_id: int,
    start_date: date = Query(..., description="Filter invoices issued on or after this date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Filter invoices issued on or before this date (YYYY-MM-DD)"),
    include_invoices: bool = Query(False, description="Whether to include the list of invoices in the response"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get account statement for a school with date range filtering (requires admin role)

    Query parameters:
    - start_date (required): Filter for invoices issued on or after this date (format: YYYY-MM-DD)
    - end_date (required): Filter for invoices issued on or before this date (format: YYYY-MM-DD)
    - include_invoices (optional, default: false): Include the list of invoices in the response
    """
    statement = AccountStatementService.get_school_statement(
        school_id, db, start_date=start_date, end_date=end_date, include_invoices=include_invoices
    )
    if not statement:
        raise HTTPException(status_code=404, detail="School not found")
    return statement
