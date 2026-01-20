"""add_indexes_for_statement_queries

Revision ID: f132d60f44f3
Revises: c2fb10ee5d1a
Create Date: 2026-01-20 09:42:50.508529

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f132d60f44f3'
down_revision: Union[str, None] = 'c2fb10ee5d1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Index for student queries by school (school statement service)
    # Used in: SELECT COUNT(*) FROM students WHERE school_id = ? AND deleted_at IS NULL
    op.create_index(
        'ix_students_school_id_deleted_at',
        'students',
        ['school_id', 'deleted_at']
    )

    # Index for invoice queries by student with date range filtering
    # Used in: SELECT * FROM invoices WHERE student_id = ? AND deleted_at IS NULL
    #          AND status != 'cancelled' AND issue_date >= ? AND issue_date <= ?
    op.create_index(
        'ix_invoices_student_id_deleted_at_status_issue_date',
        'invoices',
        ['student_id', 'deleted_at', 'status', 'issue_date']
    )

    # Index for invoice queries with date range (used with student join in school statements)
    # Used in: SELECT * FROM invoices JOIN students WHERE deleted_at IS NULL
    #          AND status != 'cancelled' AND issue_date >= ? AND issue_date <= ?
    op.create_index(
        'ix_invoices_deleted_at_status_issue_date',
        'invoices',
        ['deleted_at', 'status', 'issue_date']
    )

    # Index for payment queries by invoice
    # Used in: SELECT SUM(amount) FROM payments WHERE invoice_id = ? AND deleted_at IS NULL
    # Also used in: SELECT * FROM payments WHERE invoice_id IN (...) AND deleted_at IS NULL
    op.create_index(
        'ix_payments_invoice_id_deleted_at',
        'payments',
        ['invoice_id', 'deleted_at']
    )


def downgrade() -> None:
    op.drop_index('ix_payments_invoice_id_deleted_at', table_name='payments')
    op.drop_index('ix_invoices_deleted_at_status_issue_date', table_name='invoices')
    op.drop_index('ix_invoices_student_id_deleted_at_status_issue_date', table_name='invoices')
    op.drop_index('ix_students_school_id_deleted_at', table_name='students')
