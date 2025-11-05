from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user_core
from app.models.core import User
from app.schemas.oranization import CreateOrganizationRequest, OrganizationResponse
from app.services.organization_service import organization_service

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post(
    "", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED
)
async def create_organization(
    request: CreateOrganizationRequest,
    current_user: User = Depends(get_current_user_core),
):
    """
    Create new organization (only for core users)
    Automatically creates tenant database and syncs owner
    """
    try:
        result = await organization_service.create_organization(
            name=request.name, owner_id=current_user.id, slug=request.slug
        )
        return OrganizationResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=List[OrganizationResponse])
async def get_my_organizations(current_user: User = Depends(get_current_user_core)):
    """
    Get all organizations owned by current user (only for core users)
    """
    try:
        organizations = await organization_service.get_organizations_by_owner(
            owner_id=current_user.id
        )
        return [OrganizationResponse(**org) for org in organizations]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str, current_user: User = Depends(get_current_user_core)
):
    """
    Get organization by ID only for core-level users
    """
    try:
        from uuid import UUID

        result = await organization_service.get_organization(UUID(org_id))
        return OrganizationResponse(**result)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
