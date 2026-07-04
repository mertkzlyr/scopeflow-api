from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, EmailStr

from app.enums.organization_role import OrganizationRole

class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)

class OrganizationResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OrganizationMemberCreate(BaseModel):
    email: EmailStr
    role: OrganizationRole


class OrganizationMemberResponse(BaseModel):
    id: int
    organization_id: int
    user_id: int
    role: OrganizationRole
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)