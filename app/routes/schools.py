from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.school import SchoolCreate, SchoolRead, SchoolUpdate
from app.schemas.account_statement import SchoolAccountStatement
from app.services.school_service import SchoolService
from app.services.account_statement_service import AccountStatementService

router = APIRouter(prefix="/schools", tags=["schools"])


@router.post("/", response_model=SchoolRead, status_code=201)
def create_school(school: SchoolCreate, db: Session = Depends(get_db)):
    """Create a new school"""
    return SchoolService.create(school, db)


@router.get("/", response_model=List[SchoolRead])
def list_schools(db: Session = Depends(get_db)):
    """List all schools (excluding soft-deleted)"""
    return SchoolService.get_all(db)


@router.get("/{school_id}", response_model=SchoolRead)
def get_school(school_id: int, db: Session = Depends(get_db)):
    """Get a school by ID"""
    school = SchoolService.get_by_id(school_id, db)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school


@router.put("/{school_id}", response_model=SchoolRead)
def update_school(school_id: int, school_update: SchoolUpdate, db: Session = Depends(get_db)):
    """Update a school"""
    school = SchoolService.get_by_id(school_id, db)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return SchoolService.update(school, school_update, db)


@router.delete("/{school_id}", status_code=204)
def delete_school(school_id: int, db: Session = Depends(get_db)):
    """Soft delete a school"""
    school = SchoolService.get_by_id(school_id, db)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    SchoolService.delete(school, db)
    return None


@router.get("/{school_id}/account-statement", response_model=SchoolAccountStatement)
def get_school_account_statement(school_id: int, db: Session = Depends(get_db)):
    """Get account statement for a school"""
    statement = AccountStatementService.get_school_statement(school_id, db)
    if not statement:
        raise HTTPException(status_code=404, detail="School not found")
    return statement
