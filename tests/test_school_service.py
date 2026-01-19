import pytest
from app.services.school_service import SchoolService
from app.schemas.school import SchoolCreate, SchoolUpdate
from app.models.school import School


def test_create_school(db):
    """Test creating a new school"""
    school_data = SchoolCreate(
        name="Test School",
        contact_email="test@school.com",
        contact_phone="+1234567890"
    )

    school = SchoolService.create(school_data, db)

    assert school.id is not None
    assert school.name == "Test School"
    assert school.contact_email == "test@school.com"
    assert school.contact_phone == "+1234567890"
    assert school.deleted_at is None


def test_get_all_schools(db):
    """Test getting all schools"""
    # Create multiple schools
    school1 = SchoolService.create(
        SchoolCreate(name="School 1", contact_email="school1@test.com", contact_phone="+1111111111"),
        db
    )
    school2 = SchoolService.create(
        SchoolCreate(name="School 2", contact_email="school2@test.com", contact_phone="+2222222222"),
        db
    )

    schools = SchoolService.get_all(db)

    assert len(schools) == 2
    assert schools[0].name == "School 1"
    assert schools[1].name == "School 2"


def test_get_school_by_id(db):
    """Test getting a school by ID"""
    school = SchoolService.create(
        SchoolCreate(name="Test School", contact_email="test@school.com", contact_phone="+1234567890"),
        db
    )

    retrieved_school = SchoolService.get_by_id(school.id, db)

    assert retrieved_school is not None
    assert retrieved_school.id == school.id
    assert retrieved_school.name == "Test School"


def test_get_nonexistent_school(db):
    """Test getting a school that doesn't exist"""
    school = SchoolService.get_by_id(999, db)

    assert school is None


def test_update_school(db):
    """Test updating a school"""
    school = SchoolService.create(
        SchoolCreate(name="Original Name", contact_email="original@test.com", contact_phone="+1111111111"),
        db
    )

    update_data = SchoolUpdate(name="Updated Name", contact_email="updated@test.com")
    updated_school = SchoolService.update(school, update_data, db)

    assert updated_school.name == "Updated Name"
    assert updated_school.contact_email == "updated@test.com"
    assert updated_school.contact_phone == "+1111111111"  # Unchanged


def test_soft_delete_school(db):
    """Test soft deleting a school"""
    school = SchoolService.create(
        SchoolCreate(name="To Delete", contact_email="delete@test.com", contact_phone="+1234567890"),
        db
    )

    SchoolService.delete(school, db)

    # Should not be returned by get_by_id
    retrieved_school = SchoolService.get_by_id(school.id, db)
    assert retrieved_school is None

    # Should not be in get_all
    all_schools = SchoolService.get_all(db)
    assert len(all_schools) == 0

    # But should still exist in database with deleted_at set
    deleted_school = db.query(School).filter(School.id == school.id).first()
    assert deleted_school is not None
    assert deleted_school.deleted_at is not None


def test_get_all_excludes_soft_deleted(db):
    """Test that get_all excludes soft-deleted schools"""
    school1 = SchoolService.create(
        SchoolCreate(name="Active School", contact_email="active@test.com", contact_phone="+1111111111"),
        db
    )
    school2 = SchoolService.create(
        SchoolCreate(name="Deleted School", contact_email="deleted@test.com", contact_phone="+2222222222"),
        db
    )

    # Soft delete school2
    SchoolService.delete(school2, db)

    # get_all should only return school1
    schools = SchoolService.get_all(db)
    assert len(schools) == 1
    assert schools[0].id == school1.id
