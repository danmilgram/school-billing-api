from datetime import date

from app.models.student import Student, StudentStatus
from app.schemas.school import SchoolCreate
from app.schemas.student import StudentCreate, StudentUpdate
from app.services.school_service import SchoolService
from app.services.student_service import StudentService


def test_create_student(db):
    """Test creating a new student"""
    # Create a school first
    school = SchoolService.create(
        SchoolCreate(
            name="Test School",
            contact_email="test@school.com",
            contact_phone="+1234567890",
        ),
        db,
    )

    student_data = StudentCreate(
        school_id=school.id,
        first_name="John",
        last_name="Doe",
        email="john.doe@student.com",
        enrollment_date=date(2024, 1, 15),
        status=StudentStatus.ACTIVE,
    )

    student = StudentService.create(student_data, db)

    assert student.id is not None
    assert student.school_id == school.id
    assert student.first_name == "John"
    assert student.last_name == "Doe"
    assert student.email == "john.doe@student.com"
    assert student.enrollment_date == date(2024, 1, 15)
    assert student.status == StudentStatus.ACTIVE
    assert student.deleted_at is None


def test_get_all_students(db):
    """Test getting all students"""
    school = SchoolService.create(
        SchoolCreate(
            name="Test School",
            contact_email="test@school.com",
            contact_phone="+1234567890",
        ),
        db,
    )

    # Create multiple students
    StudentService.create(
        StudentCreate(
            school_id=school.id,
            first_name="John",
            last_name="Doe",
            email="john@student.com",
            enrollment_date=date(2024, 1, 15),
        ),
        db,
    )
    StudentService.create(
        StudentCreate(
            school_id=school.id,
            first_name="Jane",
            last_name="Smith",
            email="jane@student.com",
            enrollment_date=date(2024, 2, 1),
        ),
        db,
    )

    students = StudentService.get_all(db)

    assert len(students) == 2
    assert students[0].first_name == "John"
    assert students[1].first_name == "Jane"


def test_get_student_by_id(db):
    """Test getting a student by ID"""
    school = SchoolService.create(
        SchoolCreate(
            name="Test School",
            contact_email="test@school.com",
            contact_phone="+1234567890",
        ),
        db,
    )

    student = StudentService.create(
        StudentCreate(
            school_id=school.id,
            first_name="John",
            last_name="Doe",
            email="john@student.com",
            enrollment_date=date(2024, 1, 15),
        ),
        db,
    )

    retrieved_student = StudentService.get_by_id(student.id, db)

    assert retrieved_student is not None
    assert retrieved_student.id == student.id
    assert retrieved_student.first_name == "John"


def test_get_nonexistent_student(db):
    """Test getting a student that doesn't exist"""
    student = StudentService.get_by_id(999, db)

    assert student is None


def test_update_student(db):
    """Test updating a student"""
    school = SchoolService.create(
        SchoolCreate(
            name="Test School",
            contact_email="test@school.com",
            contact_phone="+1234567890",
        ),
        db,
    )

    student = StudentService.create(
        StudentCreate(
            school_id=school.id,
            first_name="John",
            last_name="Doe",
            email="john@student.com",
            enrollment_date=date(2024, 1, 15),
        ),
        db,
    )

    update_data = StudentUpdate(first_name="Jane", email="jane@student.com")
    updated_student = StudentService.update(student, update_data, db)

    assert updated_student.first_name == "Jane"
    assert updated_student.email == "jane@student.com"
    assert updated_student.last_name == "Doe"  # Unchanged


def test_update_student_status(db):
    """Test updating student status"""
    school = SchoolService.create(
        SchoolCreate(
            name="Test School",
            contact_email="test@school.com",
            contact_phone="+1234567890",
        ),
        db,
    )

    student = StudentService.create(
        StudentCreate(
            school_id=school.id,
            first_name="John",
            last_name="Doe",
            email="john@student.com",
            enrollment_date=date(2024, 1, 15),
            status=StudentStatus.ACTIVE,
        ),
        db,
    )

    update_data = StudentUpdate(status=StudentStatus.GRADUATED)
    updated_student = StudentService.update(student, update_data, db)

    assert updated_student.status == StudentStatus.GRADUATED


def test_soft_delete_student(db):
    """Test soft deleting a student"""
    school = SchoolService.create(
        SchoolCreate(
            name="Test School",
            contact_email="test@school.com",
            contact_phone="+1234567890",
        ),
        db,
    )

    student = StudentService.create(
        StudentCreate(
            school_id=school.id,
            first_name="John",
            last_name="Doe",
            email="john@student.com",
            enrollment_date=date(2024, 1, 15),
        ),
        db,
    )

    StudentService.delete(student, db)

    # Should not be returned by get_by_id
    retrieved_student = StudentService.get_by_id(student.id, db)
    assert retrieved_student is None

    # Should not be in get_all
    all_students = StudentService.get_all(db)
    assert len(all_students) == 0

    # But should still exist in database with deleted_at set
    deleted_student = db.query(Student).filter(Student.id == student.id).first()
    assert deleted_student is not None
    assert deleted_student.deleted_at is not None


def test_get_all_excludes_soft_deleted(db):
    """Test that get_all excludes soft-deleted students"""
    school = SchoolService.create(
        SchoolCreate(
            name="Test School",
            contact_email="test@school.com",
            contact_phone="+1234567890",
        ),
        db,
    )

    student1 = StudentService.create(
        StudentCreate(
            school_id=school.id,
            first_name="John",
            last_name="Doe",
            email="john@student.com",
            enrollment_date=date(2024, 1, 15),
        ),
        db,
    )
    student2 = StudentService.create(
        StudentCreate(
            school_id=school.id,
            first_name="Jane",
            last_name="Smith",
            email="jane@student.com",
            enrollment_date=date(2024, 2, 1),
        ),
        db,
    )

    # Soft delete student2
    StudentService.delete(student2, db)

    # get_all should only return student1
    students = StudentService.get_all(db)
    assert len(students) == 1
    assert students[0].id == student1.id
