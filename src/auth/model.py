"""Module contains models used for authentication service and routes."""
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RegisteredUserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    id: UUID


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    email_token: str
    token_type: str = "bearer"
