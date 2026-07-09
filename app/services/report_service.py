from collections import defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.organization_role import OrganizationRole
from app.enums.scope_category import ScopeCategory
from app.enums.task_status import TaskStatus
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.repositories.project_repository import (
    get_projects_for_organization,
    get_projects_for_user_in_organization,
)
from app.repositories.report_repository import get_tasks_updated_in_period_for_projects
from app.schemas.report import WeeklyProjectReport, WeeklyReportResponse
from app.services.project_service import get_current_user_organization_membership


def get_default_week_start() -> date:
    today = datetime.utcnow().date()

    return today - timedelta(days=today.weekday())


def get_week_range(week_start: date | None) -> tuple[date, date, datetime, datetime]:
    resolved_week_start = week_start or get_default_week_start()
    week_end = resolved_week_start + timedelta(days=7)

    start_at = datetime.combine(resolved_week_start, time.min)
    end_at = datetime.combine(week_end, time.min)

    return resolved_week_start, week_end, start_at, end_at


def role_can_view_all_project_reports(role: OrganizationRole) -> bool:
    return role in [
        OrganizationRole.OWNER,
        OrganizationRole.ADMIN,
    ]


def build_empty_project_report(project: Project) -> WeeklyProjectReport:
    return WeeklyProjectReport(
        project_id=project.id,
        project_name=project.name,
        total_tasks=0,
        tasks_created=0,
        approved_tasks=0,
        revision_requested_tasks=0,
        change_request_tasks=0,
        out_of_scope_tasks=0,
        billable_extra_tasks=0,
    )


def build_project_report(
    project: Project,
    tasks: list[Task],
    start_at: datetime,
    end_at: datetime,
) -> WeeklyProjectReport:
    tasks_created = [
        task
        for task in tasks
        if task.created_at >= start_at and task.created_at < end_at
    ]

    approved_tasks = [
        task for task in tasks if task.status == TaskStatus.APPROVED
    ]

    revision_requested_tasks = [
        task for task in tasks if task.status == TaskStatus.REVISION_REQUESTED
    ]

    change_request_tasks = [
        task for task in tasks if task.scope_category == ScopeCategory.CHANGE_REQUEST
    ]

    out_of_scope_tasks = [
        task for task in tasks if task.scope_category == ScopeCategory.OUT_OF_SCOPE
    ]

    billable_extra_tasks = [
        task for task in tasks if task.scope_category == ScopeCategory.BILLABLE_EXTRA
    ]

    return WeeklyProjectReport(
        project_id=project.id,
        project_name=project.name,
        total_tasks=len(tasks),
        tasks_created=len(tasks_created),
        approved_tasks=len(approved_tasks),
        revision_requested_tasks=len(revision_requested_tasks),
        change_request_tasks=len(change_request_tasks),
        out_of_scope_tasks=len(out_of_scope_tasks),
        billable_extra_tasks=len(billable_extra_tasks),
    )


def build_weekly_report_response(
    organization_id: int,
    week_start: date,
    week_end: date,
    project_reports: list[WeeklyProjectReport],
) -> WeeklyReportResponse:
    return WeeklyReportResponse(
        organization_id=organization_id,
        week_start=week_start,
        week_end=week_end,
        total_tasks=sum(report.total_tasks for report in project_reports),
        tasks_created=sum(report.tasks_created for report in project_reports),
        approved_tasks=sum(report.approved_tasks for report in project_reports),
        revision_requested_tasks=sum(
            report.revision_requested_tasks for report in project_reports
        ),
        change_request_tasks=sum(
            report.change_request_tasks for report in project_reports
        ),
        out_of_scope_tasks=sum(
            report.out_of_scope_tasks for report in project_reports
        ),
        billable_extra_tasks=sum(
            report.billable_extra_tasks for report in project_reports
        ),
        projects=project_reports,
    )


async def get_weekly_report_for_user(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
    week_start: date | None = None,
) -> WeeklyReportResponse:
    organization_member = await get_current_user_organization_membership(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
    )

    resolved_week_start, week_end, start_at, end_at = get_week_range(
        week_start=week_start,
    )

    if role_can_view_all_project_reports(organization_member.role):
        projects = await get_projects_for_organization(
            db=db,
            organization_id=organization_id,
        )
    else:
        projects = await get_projects_for_user_in_organization(
            db=db,
            organization_id=organization_id,
            user_id=current_user.id,
        )

    project_ids = [project.id for project in projects]

    tasks = await get_tasks_updated_in_period_for_projects(
        db=db,
        project_ids=project_ids,
        start_at=start_at,
        end_at=end_at,
    )

    tasks_by_project_id: dict[int, list[Task]] = defaultdict(list)

    for task in tasks:
        tasks_by_project_id[task.project_id].append(task)

    project_reports = []

    for project in projects:
        project_tasks = tasks_by_project_id.get(project.id, [])

        if not project_tasks:
            project_reports.append(build_empty_project_report(project))
            continue

        project_reports.append(
            build_project_report(
                project=project,
                tasks=project_tasks,
                start_at=start_at,
                end_at=end_at,
            )
        )

    return build_weekly_report_response(
        organization_id=organization_id,
        week_start=resolved_week_start,
        week_end=week_end,
        project_reports=project_reports,
    )