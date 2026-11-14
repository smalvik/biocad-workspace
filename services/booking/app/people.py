"""Explicit public profile projection; never expose account/session/private fields."""

from app.models import Employee


def person_public(employee: Employee) -> dict:
    return {
        "id": employee.id,
        "full_name": employee.full_name,
        "job_title": employee.job_title,
        "department": employee.department,
        "avatar_url": employee.avatar_url,
        "fictional": employee.fictional,
    }
