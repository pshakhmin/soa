import logging
import uuid
from typing import Optional

import grpc
from fastapi import APIRouter, Depends, HTTPException, Query, status
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.empty_pb2 import Empty

from app import schemas as api_schemas
from app.grpc_clients import get_promocode_stub
from app import promocode_pb2  # Import generated protobuf messages
from app.dependencies import get_current_business_user # Import the dependency

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Helper to handle gRPC errors ---
def handle_grpc_error(e: grpc.RpcError):
    """Maps gRPC errors to FastAPI HTTPExceptions."""
    if e.code() == grpc.StatusCode.NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.details())
    elif e.code() == grpc.StatusCode.ALREADY_EXISTS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.details())
    elif e.code() == grpc.StatusCode.INVALID_ARGUMENT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.details())
    elif e.code() == grpc.StatusCode.UNAUTHENTICATED:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.details())
    elif e.code() == grpc.StatusCode.PERMISSION_DENIED:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.details())
    else:
        # General internal server error for other gRPC issues
        logger.error(f"Unhandled gRPC error: {e.code()} - {e.details()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred with the promocode service.")


# --- Metadata Helper ---
def create_grpc_metadata(user_id: str) -> list[tuple[str, str]]:
    """Creates metadata including the user ID."""
    return [('x-user-id', user_id)]


# --- API Endpoints ---

@router.post(
    "/",
    response_model=api_schemas.PromocodeResponse, # Use gateway schema
    status_code=status.HTTP_201_CREATED,
    summary="Create a new promocode",
    description="Creates a new promocode. Requires business user role.",
)
async def create_promocode(
    promocode_in: api_schemas.PromocodeCreate, # Use gateway schema
    stub: promocode_pb2.PromocodeServiceStub = Depends(get_promocode_stub),
    current_user: api_schemas.UserResponse = Depends(get_current_business_user),
):
    logger.info(f"User {current_user.id} attempting to create promocode: {promocode_in.code}")
    try:
        # Prepare gRPC request
        grpc_request = promocode_pb2.CreatePromocodeRequest(
            code=promocode_in.code,
            discount_type=promocode_pb2.DiscountType.Value(promocode_in.discount_type.name),
            discount_value=promocode_in.discount_value,
            usage_limit=promocode_in.usage_limit,
        )
        # Add optional expiration date
        if promocode_in.expiration_date:
            ts = Timestamp()
            # Ensure timezone awareness if needed, gRPC expects UTC typically
            ts.FromDatetime(promocode_in.expiration_date)
            grpc_request.expiration_date.CopyFrom(ts)

        # Create metadata
        metadata = create_grpc_metadata(user_id=str(current_user.id))

        # Call gRPC service
        grpc_response = await stub.CreatePromocode(grpc_request, metadata=metadata)

        # Convert gRPC response back to Pydantic schema for HTTP response
        # Note: This assumes the structure matches. Adjust if needed.
        response_data = api_schemas.PromocodeResponseData.from_orm(grpc_response.promocode)
        return api_schemas.PromocodeResponse(promocode=response_data)

    except grpc.RpcError as e:
        handle_grpc_error(e)
    except Exception as e:
        logger.exception(f"Unexpected error creating promocode for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.get(
    "/{promocode_id}",
    response_model=api_schemas.PromocodeResponse,
    summary="Get a specific promocode by ID",
    description="Retrieves details of a specific promocode owned by the current business user.",
)
async def get_promocode(
    promocode_id: uuid.UUID,
    stub: promocode_pb2.PromocodeServiceStub = Depends(get_promocode_stub),
    current_user: api_schemas.UserResponse = Depends(get_current_business_user),
):
    logger.info(f"User {current_user.id} attempting to get promocode: {promocode_id}")
    try:
        grpc_request = promocode_pb2.GetPromocodeRequest(id=str(promocode_id))
        metadata = create_grpc_metadata(user_id=str(current_user.id))
        grpc_response = await stub.GetPromocode(grpc_request, metadata=metadata)

        response_data = api_schemas.PromocodeResponseData.from_orm(grpc_response.promocode)
        return api_schemas.PromocodeResponse(promocode=response_data)

    except grpc.RpcError as e:
        handle_grpc_error(e)
    except Exception as e:
        logger.exception(f"Unexpected error getting promocode {promocode_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.get(
    "/",
    response_model=api_schemas.ListPromocodesResponse,
    summary="List owned promocodes",
    description="Retrieves a paginated list of promocodes owned by the current business user.",
)
async def list_promocodes(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    stub: promocode_pb2.PromocodeServiceStub = Depends(get_promocode_stub),
    current_user: api_schemas.UserResponse = Depends(get_current_business_user),
):
    logger.info(f"User {current_user.id} attempting to list promocodes (page={page}, size={page_size})")
    try:
        grpc_request = promocode_pb2.ListPromocodesRequest(page=page, page_size=page_size)
        metadata = create_grpc_metadata(user_id=str(current_user.id))
        grpc_response = await stub.ListPromocodes(grpc_request, metadata=metadata)

        # Convert list of promocodes
        promocodes_data = [api_schemas.PromocodeResponseData.from_orm(p) for p in grpc_response.promocodes]

        return api_schemas.ListPromocodesResponse(
            promocodes=promocodes_data,
            total_count=grpc_response.total_count,
            page=grpc_response.page,
            page_size=grpc_response.page_size,
        )

    except grpc.RpcError as e:
        handle_grpc_error(e)
    except Exception as e:
        logger.exception(f"Unexpected error listing promocodes for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.put(
    "/{promocode_id}",
    response_model=api_schemas.PromocodeResponse,
    summary="Update a promocode",
    description="Updates details of a specific promocode owned by the current business user.",
)
async def update_promocode(
    promocode_id: uuid.UUID,
    promocode_in: api_schemas.PromocodeUpdate, # Use gateway schema
    stub: promocode_pb2.PromocodeServiceStub = Depends(get_promocode_stub),
    current_user: api_schemas.UserResponse = Depends(get_current_business_user),
):
    logger.info(f"User {current_user.id} attempting to update promocode: {promocode_id}")
    try:
        # Prepare gRPC request - only include fields that are set
        update_fields = promocode_in.model_dump(exclude_unset=True)
        if not update_fields:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update.")

        grpc_request = promocode_pb2.UpdatePromocodeRequest(id=str(promocode_id))

        if 'code' in update_fields:
            grpc_request.code = update_fields['code']
        if 'discount_type' in update_fields:
            grpc_request.discount_type = promocode_pb2.DiscountType.Value(update_fields['discount_type'].name)
        if 'discount_value' in update_fields:
            grpc_request.discount_value = update_fields['discount_value']
        if 'expiration_date' in update_fields:
             ts = Timestamp()
             # Handle None case if expiration_date can be unset
             if update_fields['expiration_date']:
                 ts.FromDatetime(update_fields['expiration_date'])
                 grpc_request.expiration_date.CopyFrom(ts)
             else:
                 # How to signal clearing the date? Proto uses optional.
                 # Check if setting an empty Timestamp works or if specific handling is needed.
                 # For now, assume setting it clears it if None is passed in Pydantic.
                 # If proto requires explicit null/clear, adjust this.
                 pass # Or grpc_request.ClearField('expiration_date') if available
        if 'usage_limit' in update_fields:
            grpc_request.usage_limit = update_fields['usage_limit']
        if 'is_active' in update_fields:
            grpc_request.is_active = update_fields['is_active']

        metadata = create_grpc_metadata(user_id=str(current_user.id))
        grpc_response = await stub.UpdatePromocode(grpc_request, metadata=metadata)

        response_data = api_schemas.PromocodeResponseData.from_orm(grpc_response.promocode)
        return api_schemas.PromocodeResponse(promocode=response_data)

    except grpc.RpcError as e:
        handle_grpc_error(e)
    except Exception as e:
        logger.exception(f"Unexpected error updating promocode {promocode_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.delete(
    "/{promocode_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a promocode",
    description="Deletes a specific promocode owned by the current business user.",
)
async def delete_promocode(
    promocode_id: uuid.UUID,
    stub: promocode_pb2.PromocodeServiceStub = Depends(get_promocode_stub),
    current_user: api_schemas.UserResponse = Depends(get_current_business_user),
):
    logger.info(f"User {current_user.id} attempting to delete promocode: {promocode_id}")
    try:
        grpc_request = promocode_pb2.DeletePromocodeRequest(id=str(promocode_id))
        metadata = create_grpc_metadata(user_id=str(current_user.id))
        await stub.DeletePromocode(grpc_request, metadata=metadata)
        # No content to return on success
        return None

    except grpc.RpcError as e:
        handle_grpc_error(e)
    except Exception as e:
        logger.exception(f"Unexpected error deleting promocode {promocode_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")
