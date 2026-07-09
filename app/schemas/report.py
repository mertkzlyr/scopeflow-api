from datetime import date

from pydantic import BaseModel


class WeeklyProjectReport(BaseModel):
    project_id: int
    project_name: str

    total_tasks: int
    tasks_created: int

    approved_tasks: int
    revision_requested_tasks: int

    change_request_tasks: int
    out_of_scope_tasks: int
    billable_extra_tasks: int


class WeeklyReportResponse(BaseModel):
    organization_id: int

    week_start: date
    week_end: date

    total_tasks: int
    tasks_created: int

    approved_tasks: int
    revision_requested_tasks: int

    change_request_tasks: int
    out_of_scope_tasks: int
    billable_extra_tasks: int

    projects: list[WeeklyProjectReport]