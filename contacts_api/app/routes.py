from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from contacts_api.app import crud
from contacts_api.app.database import get_db
from contacts_api.app.schemas import ContactCreate, ContactUpdate, ContactOut, UserCreate, UserResponse
from contacts_api.app.dependencies import get_current_user
from contacts_api.app.models import User
from contacts_api.app.crud import create_user

router = APIRouter(prefix="/api/contacts", tags=["Contacts"])


@router.post("/", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await crud.create_contact(contact, db, current_user)


@router.get("/", response_model=List[ContactOut])
async def get_contacts(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await crud.get_contacts(skip, limit, db, current_user)


@router.get("/{contact_id}", response_model=ContactOut)
async def get_contact_by_id(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = await crud.get_contact(contact_id, db, current_user)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.put("/{contact_id}", response_model=ContactOut)
async def update_contact(
    contact_id: int,
    updated_data: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = await crud.update_contact(contact_id, updated_data, db, current_user)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = await crud.delete_contact(contact_id, db, current_user)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")


@router.get("/search/", response_model=List[ContactOut])
async def search_contacts(
    query: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await crud.search_contacts(query, db, current_user)


@router.get("/birthdays/upcoming", response_model=List[ContactOut])
async def upcoming_birthdays(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await crud.get_upcoming_birthdays(db, current_user)

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, db: AsyncSession = Depends(get_db)):
    return await create_user(user, db)