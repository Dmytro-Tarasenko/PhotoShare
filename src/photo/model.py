from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class PhotoBase(BaseModel):
    title: str
    url: str
    author_id: int


class PhotoCreate(PhotoBase):
    pass


class PhotoUpdate(PhotoBase):
    completed: bool


class PhotoResponse(PhotoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
