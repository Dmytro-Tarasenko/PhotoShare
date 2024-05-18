from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from comment.model import CommentModel
from tags.model import TagModel


class PhotoModel(BaseModel):
    description: Optional[str] = None



class PhotoCreate(PhotoModel):
    pass


class PhotoUpdate(PhotoModel):
    description: Optional[str] = None


class PhotoResponse(PhotoModel):
    id: int
    url: str
    public_id: str
    author_fk: int
    comments: List[CommentModel] = []
    tags: List[TagModel] = []

    model_config = ConfigDict(from_attributes=True)
