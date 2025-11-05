
from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.api.deps import get_current_user_tenant
from app.config import get_settings
from app.models.tenant import TenantUser
from app.schemas.user import (
    TenantUserProfileResponse,
    UpdateProfileRequest,
)
from app.services.user_service import user_service

settings = get_settings()
router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=TenantUserProfileResponse)
async def get_my_profile(
    x_tenant_id: str | None = Header(None, alias=settings.TENANT_HEADER_NAME),
    user_tenant: tuple[TenantUser, str] = Depends(get_current_user_tenant),
):
    """
    Get current user profile (only for tenant-level users)
    Requires X-Tenant-Id header and tenant JWT token
    """
    user, tenant_id = user_tenant

    try:
        result = await user_service.get_tenant_user_profile(
            user_id=user.id, tenant_id=tenant_id
        )
        return TenantUserProfileResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/me", response_model=TenantUserProfileResponse)
async def update_my_profile(
    request: UpdateProfileRequest,
    x_tenant_id: str | None = Header(None, alias=settings.TENANT_HEADER_NAME),
    user_tenant: tuple[TenantUser, str] = Depends(get_current_user_tenant),
):
    """
    Update current user profile (only for tenant-level users)
    Requires X-Tenant-Id header and tenant JWT token
    """
    user, tenant_id = user_tenant

    try:
        update_data = {}
        if request.full_name is not None:
            update_data["full_name"] = request.full_name
        if request.phone is not None:
            update_data["phone"] = request.phone
        if request.avatar_url is not None:
            update_data["avatar_url"] = request.avatar_url
        if request.metadata is not None:
            update_data["metadata"] = request.metadata

        result = await user_service.update_tenant_user_profile(
            user_id=user.id, tenant_id=tenant_id, **update_data
        )
        return TenantUserProfileResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
