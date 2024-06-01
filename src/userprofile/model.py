from datetime import datetime, timezone
from typing import Optional, Any, Annotated

import pydantic
from pydantic import (BaseModel, EmailStr,
                      PastDate, computed_field,
                      Field, PositiveInt,
                      ConfigDict, ValidationInfo)
from pydantic.functional_validators import BeforeValidator, field_validator

from userprofile.orm import Role, UserORM


class UserProfileModel(BaseModel):
    """
    Model that holds all user information
    """
    model_config = ConfigDict(from_attributes=True,
                              validate_assignment=True)

    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: EmailStr
    birthday: Optional[PastDate]
    registered_at: datetime = Field(default=datetime.now(timezone.utc))
    is_banned: bool = Field(default=False)
    role: Role = Field(default='user')
    photos: int = Field(default=0, ge=0)
    comments: int = Field(default=0, ge=0)

    @computed_field
    @property
    def full_name(self) -> str:
        """
        Fields value is computed by concatenation of first_name
        and not empty last_name

        Returns:
            str: Full name
        """
        lname = ' ' + self.last_name if self.last_name else ''
        return self.first_name + lname


class UserPublicProfileModel(BaseModel):
    """
    Model that holds public user information
    """
    model_config = ConfigDict(from_attributes=True)
    username: str = Field()
    first_name: str
    last_name: Optional[str]
    registered_at: datetime = Field(default=datetime.now(timezone.utc))
    role: Role = Field(default='user')
    photos: int = Field(ge=0, default=0)
    comments: int = Field(ge=0, default=0)

    @computed_field
    @property
    def full_name(self) -> str:
        """
        Fields value is computed by concatenation of first_name
        and not empty last_name

        Returns:
            str: Full name
        """
        lname = ' ' + self.last_name if self.last_name else ''
        return self.first_name + lname


class UserEditableProfileModel(BaseModel):
    username: Optional[str] = Field(min_length=3, default=None)
    email: Optional[EmailStr] = Field(default=None)
    birthday: Optional[PastDate] = Field(default=None)
    first_name: Optional[str] = Field(min_length=3, default=None)
    last_name: Optional[str] = Field(min_length=3, default=None)
