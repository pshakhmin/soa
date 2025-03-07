import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.config import settings
from app import schemas

router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: schemas.UserCreate):
    """
    Register a new user
    """
    body = user.dict()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.USER_SERVICE_URL}/api/v1/users/register", json=body
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Get access and refresh tokens
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.USER_SERVICE_URL}/api/v1/users/token", data=dict(form_data)
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )


@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(refresh_token: schemas.RefreshToken):
    """
    Refresh access token
    """
    body = refresh_token.dict()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.USER_SERVICE_URL}/api/v1/users/refresh", json=body
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )


@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(request: Request):
    """
    Get current user profile
    """
    headers = dict(request.headers)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.USER_SERVICE_URL}/api/v1/users/me", headers=headers
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )


@router.put("/me", response_model=schemas.UserResponse)
async def update_user_me(user_update: schemas.UserUpdate, request: Request):
    """
    Update current user profile
    """
    body = user_update.dict(exclude_unset=True)
    headers = dict(request.headers)
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{settings.USER_SERVICE_URL}/api/v1/users/me", json=body, headers=headers
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )
