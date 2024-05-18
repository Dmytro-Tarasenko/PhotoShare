from typing import List

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, APIRouter, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import cloudinary
from cloudinary.uploader import upload, destroy
from database import get_db
from photo.model import PhotoCreate, PhotoResponse, PhotoUpdate
from photo.orm import PhotoORM
from user_profile.orm import ProfileORM
from settings import settings


router = APIRouter(prefix='/photos', tags=["photos"])


@router.post("/", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def create_photo(photo: PhotoCreate, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )
    cloudinary_result = upload(file.file, folder="photos/")
    photo.url = cloudinary_result['secure_url']
    photo.public_id = cloudinary_result['public_id']
    photo.author_fk = 1
    db_photo = PhotoORM(**photo.dict())
    db.add(db_photo)
    await db.commit()
    await db.refresh(db_photo)
    return db_photo


@router.get("/tag/{tag}", response_model=List[PhotoResponse])
async def get_photos_by_tag_in_description(tag: str, db: AsyncSession = Depends(get_db)):
    query = select(PhotoORM).where(PhotoORM.description.contains(tag))
    result = await db.execute(query)
    photos = result.scalars().all()

    if not photos:
        raise HTTPException(status_code=404, detail="Photos not found")

    return [PhotoResponse.from_orm(photo) for photo in photos]


@router.get("/{photo_id}", response_model=PhotoResponse)
async def get_photo(photo_id: int, db: AsyncSession = Depends(get_db)):
    query = select(PhotoORM).filter_by(id=photo_id)
    result = await db.execute(query)
    db_photo = result.scalars().first()

    if not db_photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return db_photo


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(photo_id: int, db: AsyncSession = Depends(get_db)):
    query = select(PhotoORM).filter_by(id=photo_id)
    result = await db.execute(query)
    photo = result.scalars().first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    destroy(photo.public_id)

    await db.delete(photo)
    await db.commit()

    return {"detail": "Photo deleted"}


@router.put("/{photo_id}", response_model=PhotoResponse)
async def update_photo(photo_id: int, photo: PhotoUpdate, db: AsyncSession = Depends(get_db)):
    query = select(PhotoORM).filter_by(id=photo_id)
    result = await db.execute(query)
    db_photo = result.scalars().first()
    if not db_photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    db_photo.description = photo.description
    await db.commit()
    await db.refresh(db_photo)
    return db_photo
