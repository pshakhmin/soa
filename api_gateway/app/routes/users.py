import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.config import settings

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(request: Request):
    """
    Proxy endpoint for user registration
    """
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.USER_SERVICE_URL}/api/v1/users/register", json=body
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )


@router.post("/token")
async def login_for_access_token(request: Request):
    """
    Proxy endpoint for token generation
    """
    form_data = await request.form()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.USER_SERVICE_URL}/api/v1/users/token", data=dict(form_data)
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )


@router.post("/refresh")
async def refresh_token(request: Request):
    """
    Proxy endpoint for token refresh
    """
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.USER_SERVICE_URL}/api/v1/users/refresh", json=body
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )


@router.get("/me")
async def read_users_me(request: Request):
    """
    Proxy endpoint to get current user
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


@router.put("/me")
async def update_user_me(request: Request):
    """
    Proxy endpoint to update current user
    """
    body = await request.json()
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
