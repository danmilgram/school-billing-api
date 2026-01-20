"""use_partial_indexes_for_statement_queries

Revision ID: e48c2c0b9fed
Revises: f132d60f44f3
Create Date: 2026-01-20 09:45:56.667375

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e48c2c0b9fed'
down_revision: Union[str, None] = 'f132d60f44f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old inefficient indexes
    op.drop_index('ix_students_school_id_deleted_at', table_name='students')
    op.drop_index('ix_invoices_student_id_deleted_at_status_issue_date', table_name='invoices')
    op.drop_index('ix_invoices_deleted_at_status_issue_date', table_name='invoices')
    op.drop_index('ix_payments_invoice_id_deleted_at', table_name='payments')

    # Create partial indexes (more efficient - only indexes active rows)

    # Index for counting students by school (school statement service)
    # Used in: SELECT COUNT(*) FROM students WHERE school_id = ? AND deleted_at IS NULL
    op.execute("""
        CREATE INDEX ix_students_school_id_active
        ON students (school_id)
        WHERE deleted_at IS NULL
    """)

    # Index for student invoices with date range filtering
    # Used in: SELECT * FROM invoices WHERE student_id = ? AND deleted_at IS NULL
    #          AND status != 'cancelled' AND issue_date >= ? AND issue_date <= ?
    op.execute("""
        CREATE INDEX ix_invoices_student_issue_date_active
        ON invoices (student_id, issue_date)
        WHERE deleted_at IS NULL AND status != 'CANCELLED'
    """)

    # Index for invoice date range queries (used with student join in school statements)
    # Used in: SELECT * FROM invoices JOIN students WHERE deleted_at IS NULL
    #          AND status != 'cancelled' AND issue_date >= ? AND issue_date <= ?
    op.execute("""
        CREATE INDEX ix_invoices_issue_date_active
        ON invoices (issue_date)
        WHERE deleted_at IS NULL AND status != 'CANCELLED'
    """)

    # Index for payment queries by invoice (only active payments)
    # Used in: SELECT SUM(amount) FROM payments WHERE invoice_id = ? AND deleted_at IS NULL
    # Also used in: SELECT * FROM payments WHERE invoice_id IN (...) AND deleted_at IS NULL
    op.execute("""
        CREATE INDEX ix_payments_invoice_id_active
        ON payments (invoice_id)
        WHERE deleted_at IS NULL
    """)


def downgrade() -> None:
    # Drop partial indexes
    op.drop_index('ix_payments_invoice_id_active', table_name='payments')
    op.drop_index('ix_invoices_issue_date_active', table_name='invoices')
    op.drop_index('ix_invoices_student_issue_date_active', table_name='invoices')
    op.drop_index('ix_students_school_id_active', table_name='students')

    # Recreate old indexes
    op.create_index(
        'ix_students_school_id_deleted_at',
        'students',
        ['school_id', 'deleted_at']
    )
    op.create_index(
        'ix_invoices_student_id_deleted_at_status_issue_date',
        'invoices',
        ['student_id', 'deleted_at', 'status', 'issue_date']
    )
    op.create_index(
        'ix_invoices_deleted_at_status_issue_date',
        'invoices',
        ['deleted_at', 'status', 'issue_date']
    )
    op.create_index(
        'ix_payments_invoice_id_deleted_at',
        'payments',
        ['invoice_id', 'deleted_at']
    )
