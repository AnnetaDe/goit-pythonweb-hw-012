from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from datetime import date, timedelta

from contacts_api.app.models import Contact, User
from contacts_api.app.schemas import ContactCreate, ContactUpdate, UserCreate
from contacts_api.app.hashing import Hasher
from typing import Optional


# Створити контакт
async def create_contact(contact: ContactCreate, db: AsyncSession, user: User) -> Contact:
    new_contact = Contact(**contact.dict(), user_id=user.id)
    db.add(new_contact)
    await db.commit()
    await db.refresh(new_contact)
    return new_contact


# Отримати список усіх контактів користувача
async def get_contacts(skip: int, limit: int, db: AsyncSession, user: User):
    result = await db.execute(
        select(Contact)
        .filter(Contact.user_id == user.id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


# Отримати один контакт за ID (якщо належить користувачу)
async def get_contact(contact_id: int, db: AsyncSession, user: User):
    result = await db.execute(
        select(Contact)
        .filter(Contact.id == contact_id, Contact.user_id == user.id)
    )
    return result.scalar_one_or_none()


# Оновити контакт
async def update_contact(contact_id: int, updated: ContactUpdate, db: AsyncSession, user: User):
    result = await db.execute(
        select(Contact)
        .filter(Contact.id == contact_id, Contact.user_id == user.id)
    )
    contact = result.scalar_one_or_none()

    if contact:
        for key, value in updated.dict(exclude_unset=True).items():
            setattr(contact, key, value)
        await db.commit()
        await db.refresh(contact)
    return contact


# Видалити контакт
async def delete_contact(contact_id: int, db: AsyncSession, user: User):
    result = await db.execute(
        select(Contact)
        .filter(Contact.id == contact_id, Contact.user_id == user.id)
    )
    contact = result.scalar_one_or_none()

    if contact:
        await db.delete(contact)
        await db.commit()
    return contact


# Пошук контактів (ім’я, прізвище, email)
async def search_contacts(query: str, db: AsyncSession, user: User):
    result = await db.execute(
        select(Contact)
        .where(
            Contact.user_id == user.id,
            or_(
                Contact.first_name.ilike(f"%{query}%"),
                Contact.last_name.ilike(f"%{query}%"),
                Contact.email.ilike(f"%{query}%"),
            )
        )
    )
    return result.scalars().all()


# Контакти з днями народження на найближчі 7 днів
async def get_upcoming_birthdays(db: AsyncSession, user: User):
    today = date.today()
    in_seven_days = today + timedelta(days=7)

    result = await db.execute(
        select(Contact)
        .where(
            Contact.user_id == user.id,
            Contact.birthday.isnot(None),
            Contact.birthday.between(today, in_seven_days)
        )
    )
    return result.scalars().all()


async def get_contact_by_id(contact_id: int, user: User, db: AsyncSession) -> Optional[Contact]:
    result = await db.execute(
        select(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id)
    )
    return result.scalar_one_or_none()

async def create_user(user_data: UserCreate, db: AsyncSession) -> User:
    new_user = User(
        email=user_data.email,
        password=Hasher.get_password_hash(user_data.password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user