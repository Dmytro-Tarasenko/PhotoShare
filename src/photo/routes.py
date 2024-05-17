from fastapi import APIRouter, HTTPException, Depends,  Path, Query, UploadFile, File
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
import cloudinary
from cloudinary import uploader
from src.database import get_db
from src.settings import settings
from src.photo.orm import Photo

from src.photo.model import PhotoResponse
from src.photo.model import PhotoCreate
from src.photo.model import PhotoUpdate


router = APIRouter(prefix='/photos', tags=["photos"])


@router.post("/photos/", response_model=PhotoResponse)
def create_photo(photo: PhotoCreate, file: UploadFile = File(), db: AsyncSession = Depends(get_db)):
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )
    try:
        result = uploader.upload(file.file, folder="photos")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error uploading images: {e}")
    # Створення нового об'єкту фотографії
    db_photo = Photo(title=photo.title, url=result['url'], author_id=photo.author_id)
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    return db_photo

