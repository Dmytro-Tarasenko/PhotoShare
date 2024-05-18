from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
from model import CommentModel, CommentCreate, CommentUpdate
from orm import CommentORM
from photo.orm import PhotoORM
from user_profile.orm import ProfileORM
from auth.service import Authentication
from user_profile.model import UserProfileModel

router = APIRouter(
    prefix="/comments",
    tags=["comments"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[CommentModel])
async def read_comments(db: AsyncSession = Depends(get_db), skip: int = 0, limit: int = 100):
    result = await db.execute(db.query(CommentORM).offset(skip).limit(limit))
    comments = result.scalars().all()
    return comments

@router.post("/add", response_model=CommentModel)
async def create_comment(comment: CommentCreate, db: AsyncSession = Depends(get_db), current_user: UserProfileModel = Depends(Authentication().get_user)):
    if current_user.role not in ["registered_user", "moderator", "admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    author = await db.query(ProfileORM).filter(ProfileORM.id == comment.author_profile_id).first()
    photo = await db.query(PhotoORM).filter(PhotoORM.id == comment.photo_id).first()
    
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    db_comment = CommentORM(
        text=comment.text,
        author=author,
        photo=photo
    )
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    return db_comment

@router.patch("/edit/{comment_id}", response_model=CommentModel)
async def update_comment(comment_id: int, comment: CommentUpdate, db: AsyncSession = Depends(get_db), current_user: UserProfileModel = Depends(Authentication().get_user)):
    if current_user.role not in ["registered_user", "moderator", "admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db_comment = await db.query(CommentORM).filter(CommentORM.id == comment_id).first()
    if db_comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if db_comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    for var, value in vars(comment).items():
        setattr(db_comment, var, value) if value else None

    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    return db_comment

@router.delete("/delete/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: int, db: AsyncSession = Depends(get_db), current_user: UserProfileModel = Depends(Authentication().get_user)):
    if current_user.role not in ["moderator", "admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db_comment = await db.query(CommentORM).filter(CommentORM.id == comment_id).first()
    if db_comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")

    await db.delete(db_comment)
    await db.commit()
    return None