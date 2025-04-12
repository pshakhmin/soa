import uuid
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer

from app.config import settings
from app import schemas as api_schemas # Rename to avoid conflict with user service schemas if needed

# This scheme expects the token to be sent in the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/token") # Points to the gateway's token endpoint

async def get_current_user_data(
    request: Request,
    token: str = Depends(oauth2_scheme) # Extracts token from Authorization header
) -> api_schemas.UserResponse: # Using UserResponse schema defined in gateway
    """
    Dependency to get current user data by calling the user_service/me endpoint.

    In a real scenario, you might decode the JWT token directly in the gateway
    if it shares the secret key, avoiding the extra HTTP call.
    """
    headers = {'Authorization': f'Bearer {token}'}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.USER_SERVICE_URL}/api/v1/users/me", headers=headers
            )
            response.raise_for_status() # Raise exception for 4xx/5xx errors
            user_data = response.json()
            # Assuming user_service returns data compatible with api_gateway UserResponse schema
            # You might need more robust parsing/validation here
            return api_schemas.UserResponse(**user_data)
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error connecting to user service: {exc}",
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == status.HTTP_401_UNAUTHORIZED:
                 raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            # Re-raise other HTTP errors from user service
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=exc.response.text,
            )
        except Exception as e: # Catch potential parsing errors etc.
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred while fetching user data: {e}",
            )


async def get_current_business_user(
    current_user: api_schemas.UserResponse = Depends(get_current_user_data)
) -> api_schemas.UserResponse:
    """
    Dependency that ensures the current user is authenticated and has a 'business' role.
    Placeholder: Assumes 'role' field exists in UserResponse. Adjust if needed.
    """
    # !!! IMPORTANT: Adjust this check based on how 'role' is actually stored/returned !!!
    # Example: Check a 'role' attribute. This might not exist in your current UserResponse schema.
    # You might need to add 'role' to user_service models/schemas and the response.
    # if not hasattr(current_user, 'role') or current_user.role != "business":
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Operation not permitted. Business account required.",
    #     )

    # --- TEMPORARY Placeholder Check ---
    # Remove this once role check is properly implemented based on your User model
    print(f"WARNING: Business role check is currently bypassed for user {current_user.id}")
    # --- End Placeholder ---

    # Check if user is active (example based on existing schema)
    if not current_user.is_active:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return current_user

# You might need a simpler dependency if you only need the user ID
async def get_current_user_id(
    current_user: api_schemas.UserResponse = Depends(get_current_user_data)
) -> str:
     """Dependency to get just the current user's ID."""
     return current_user.id
