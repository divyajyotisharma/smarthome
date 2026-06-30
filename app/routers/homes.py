"""Home context lookup route for the seeded demo client."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Home
from app.schemas import HomeResponse


router = APIRouter(prefix="/homes", tags=["homes"])


@router.get("/{home_id}", response_model=HomeResponse)
def get_home(home_id: int, session: Session = Depends(get_session)) -> Home:
    """Expose the default demo home so reviewers can confirm seeding."""

    home = session.get(Home, home_id)
    if home is None:
        raise HTTPException(status_code=404, detail="Home not found")
    return home
