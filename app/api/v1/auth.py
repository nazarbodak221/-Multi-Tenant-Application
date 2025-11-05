from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_tenant_id
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED
)
async def register(request: RegisterRequest, tenant_id: Optional[str] = Depends(get_tenant_id)):
    """
    Register a new user

    Routing logic:
    - If X-Tenant-Id header is present: register tenant user
    - If X-Tenant-Id header is absent: register core (platform) user
    """
    try:
        if tenant_id:
            result = await auth_service.register_tenant_user(
                tenant_id=tenant_id,
                email=request.email,
                password=request.password,
                full_name=request.full_name,
            )
        else:
            result = await auth_service.register_core_user(
                email=request.email,
                password=request.password,
                full_name=request.full_name,
            )

        return AuthResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, tenant_id: Optional[str] = Depends(get_tenant_id)):
    """
    Login user

    Routing logic:
    - If X-Tenant-Id header is present: login tenant user
    - If X-Tenant-Id header is absent: login core (platform) user
    """
    try:
        if tenant_id:
            result = await auth_service.login_tenant_user(
                tenant_id=tenant_id, email=request.email, password=request.password
            )
        else:
            result = await auth_service.login_core_user(
                email=request.email, password=request.password
            )

        return AuthResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
