from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, APIRouter, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import cloudinary
from cloudinary.uploader import upload
from database import get_db
from photo.model import PhotoCreate, PhotoResponse
from photo.orm import PhotoORM
from user_profile.orm import ProfileORM
from settings import settings


router = APIRouter(prefix='/photos', tags=["photos"])


@router.post("/photos/", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def create_photo(photo: PhotoCreate, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )
    cloudinary_result = upload(file.file, folder="photos/")
    photo.url = cloudinary_result['secure_url']
    photo.author_fk = 1
    db_photo = PhotoORM(**photo.dict())
    db.add(db_photo)
    await db.commit()
    await db.refresh(db_photo)

    return db_photo
