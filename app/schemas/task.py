from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, EmailStr

from app.enums.scope_category import ScopeCategory
from app.enums.task_status import TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    scope_category: ScopeCategory = ScopeCategory.ORIGINAL_SCOPE

class TaskStatusUpdate(BaseModel):
    status: TaskStatus

class TaskAssign(BaseModel):
    email: EmailStr


class TaskResponse(BaseModel):
    id: int
    project_id: int
    created_by_user_id: int | None
    assigned_to_user_id: int | None
    title: str
    description: str | None
    status: TaskStatus
    scope_category: ScopeCategory
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)