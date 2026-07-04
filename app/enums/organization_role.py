from enum import Enum

class OrganizationRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    ClIENT = "client"
    VIEWER = "viewer"