from enum import Enum


class AuditAction(str, Enum):
    ORGANIZATION_CREATED = "organization_created"
    ORGANIZATION_MEMBER_ADDED = "organization_member_added"

    PROJECT_CREATED = "project_created"
    PROJECT_MEMBER_ADDED = "project_member_added"

    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_UPDATED = "task_updated"

    COMMENT_CREATED = "comment_created"