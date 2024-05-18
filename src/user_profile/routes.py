from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from user_profile.model import UserProfileModel
from database import get_db
from auth.service import Authentication

router = APIRouter()

@router.get("/profile", response_model=UserProfileModel)
async def get_profile(current_user: Optional[UserProfileModel] = Depends(Authentication().get_user), db: Optional[AsyncSession] = Depends(get_db)):
    if current_user is None or db is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    result = await db.execute(db.query(UserProfileModel).filter(UserProfileModel.id == current_user.id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.put("/profile/add/{field}/{value}")
async def add_to_profile(field: str, value: str, current_user: Optional[UserProfileModel] = Depends(Authentication().get_user), db: Optional[AsyncSession] = Depends(get_db)):
    if current_user is None or db is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    result = await db.execute(db.query(UserProfileModel).filter(UserProfileModel.id == current_user.id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return {"message": "Field added successfully"}

@router.patch("/profile/edit/{field}/{value}")
async def edit_profile(field: str, value: str, current_user: Optional[UserProfileModel] = Depends(Authentication().get_user), db: Optional[AsyncSession] = Depends(get_db)):
    if current_user is None or db is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    result = await db.execute(db.query(UserProfileModel).filter(UserProfileModel.id == current_user.id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return {"message": "Profile updated successfully"}

@router.post("/profile/create", response_model=UserProfileModel)
async def create_profile(user: UserProfileModel, current_user: Optional[UserProfileModel] = Depends(Authentication().get_user), db: Optional[AsyncSession] = Depends(get_db)):
    if current_user is None or db is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    db_user = UserProfileModel(**user.dict())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.delete("/profile/delete")
async def delete_profile(current_user: Optional[UserProfileModel] = Depends(Authentication().get_user), db: Optional[AsyncSession] = Depends(get_db)):
    if current_user is None or db is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    result = await db.execute(db.query(UserProfileModel).filter(UserProfileModel.id == current_user.id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await db.delete(user)
    await db.commit()
    return {"message": "Profile deleted successfully"}