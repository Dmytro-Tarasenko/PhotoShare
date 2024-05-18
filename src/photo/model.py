from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from comment.orm import CommentORM
from tags.orm import TagORM


class PhotoModel(BaseModel):
    description: Optional[str] = None



class PhotoCreate(PhotoModel):
    pass


class PhotoUpdate(PhotoModel):
    description: Optional[str] = None


class PhotoResponse(PhotoModel):
    id: int
    url: str
    author_fk: int
    comments: List[CommentORM] = []
    tags: List[TagORM] = []

    model_config = ConfigDict(from_attributes=True)
