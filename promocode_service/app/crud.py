from typing import List, Optional, Tuple
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, select

from . import models, schemas

def create_promocode(db: Session, promocode: schemas.PromocodeCreate, owner_id: uuid.UUID) -> models.Promocode:
    """
    Creates a new promocode in the database.
    """
    db_promocode = models.Promocode(
        **promocode.model_dump(),
        owner_id=owner_id
    )
    db.add(db_promocode)
    db.commit()
    db.refresh(db_promocode)
    return db_promocode

def get_promocode_by_id(db: Session, promocode_id: uuid.UUID, owner_id: uuid.UUID) -> Optional[models.Promocode]:
    """
    Gets a specific promocode by its ID, ensuring it belongs to the owner.
    """
    return db.query(models.Promocode).filter(
        models.Promocode.id == promocode_id,
        models.Promocode.owner_id == owner_id
    ).first()

def get_promocode_by_code(db: Session, code: str) -> Optional[models.Promocode]:
    """
    Gets a promocode by its unique code. Useful for checking duplicates.
    Note: This does not check ownership.
    """
    return db.query(models.Promocode).filter(models.Promocode.code == code).first()


def get_promocodes_by_owner(
    db: Session, owner_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> Tuple[List[models.Promocode], int]:
    """
    Gets a list of promocodes owned by a specific user with pagination.
    Returns the list of promocodes and the total count for that owner.
    """
    query = db.query(models.Promocode).filter(models.Promocode.owner_id == owner_id)

    # Get the total count before applying pagination
    total_count_query = select(func.count()).select_from(query.subquery())
    total_count = db.execute(total_count_query).scalar_one()

    # Apply ordering and pagination
    promocodes = query.order_by(desc(models.Promocode.created_at)).offset(skip).limit(limit).all()

    return promocodes, total_count


def update_promocode(
    db: Session, promocode_id: uuid.UUID, promocode_update: schemas.PromocodeUpdate, owner_id: uuid.UUID
) -> Optional[models.Promocode]:
    """
    Updates an existing promocode, ensuring it belongs to the owner.
    """
    db_promocode = get_promocode_by_id(db=db, promocode_id=promocode_id, owner_id=owner_id)
    if not db_promocode:
        return None

    update_data = promocode_update.model_dump(exclude_unset=True) # Get only provided fields

    # Check for code uniqueness if code is being updated to a new value
    if "code" in update_data and update_data["code"] != db_promocode.code:
        existing_code = get_promocode_by_code(db, update_data["code"])
        if existing_code:
            # Or raise a specific exception to be handled by the gRPC server
            return None # Indicate conflict or failure

    for key, value in update_data.items():
        setattr(db_promocode, key, value)

    db.add(db_promocode)
    db.commit()
    db.refresh(db_promocode)
    return db_promocode

def delete_promocode(db: Session, promocode_id: uuid.UUID, owner_id: uuid.UUID) -> bool:
    """
    Deletes a promocode by its ID, ensuring it belongs to the owner.
    Returns True if deletion was successful, False otherwise.
    """
    db_promocode = get_promocode_by_id(db=db, promocode_id=promocode_id, owner_id=owner_id)
    if not db_promocode:
        return False

    db.delete(db_promocode)
    db.commit()
    return True

# Add other potential CRUD functions if needed, e.g., for applying/validating promocodes
# def apply_promocode(db: Session, code: str, user_id: uuid.UUID) -> Optional[models.Promocode]:
#     """ Example: Find an active promocode and increment its usage count """
#     promocode = db.query(models.Promocode).filter(
#         models.Promocode.code == code,
#         models.Promocode.is_active == True,
#         (models.Promocode.expiration_date == None) | (models.Promocode.expiration_date > func.now()),
#         (models.Promocode.usage_limit == 0) | (models.Promocode.usage_count < models.Promocode.usage_limit)
#     ).first()
#
#     if promocode:
#         promocode.usage_count += 1
#         db.add(promocode)
#         # Potentially log the usage in a separate table
#         db.commit()
#         db.refresh(promocode)
#         return promocode
#     return None
