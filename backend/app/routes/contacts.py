from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.database import get_db
from app.models.emergency_contact import EmergencyContact
from app.models.user import User
from app.auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["contacts"])

# Pydantic schemas
class EmergencyContactCreate(BaseModel):
    name: str
    phone_number: str
    email: Optional[EmailStr] = None
    relationship: Optional[str] = None

class EmergencyContactResponse(BaseModel):
    id: int
    name: str
    phone_number: str
    email: Optional[str]
    relationship: Optional[str]

    class Config:
        from_attributes = True

# Add a trusted contact
@router.post("/", response_model=EmergencyContactResponse, status_code=201)
def create_contact(
    contact_data: EmergencyContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_contact = EmergencyContact(
        user_id=current_user.id,
        name=contact_data.name,
        phone_number=contact_data.phone_number,
        email=contact_data.email,
        relationship=contact_data.relationship,
    )

    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)

    return new_contact

# List the current user's trusted contacts
@router.get("/", response_model=list[EmergencyContactResponse])
def list_contacts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contacts = (
        db.query(EmergencyContact)
        .filter(EmergencyContact.user_id == current_user.id)
        .order_by(EmergencyContact.created_at.asc())
        .all()
    )
    return contacts

# Remove a trusted contact
@router.delete("/{contact_id}", status_code=204)
def delete_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = (
        db.query(EmergencyContact)
        .filter(EmergencyContact.id == contact_id, EmergencyContact.user_id == current_user.id)
        .first()
    )

    # 404 (not 403) whether the contact doesn't exist or belongs to another
    # user, so we don't leak which contact IDs exist.
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(contact)
    db.commit()
