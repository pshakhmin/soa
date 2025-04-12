import logging
import uuid
from concurrent import futures

import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.empty_pb2 import Empty

# Import generated gRPC files
from . import promocode_pb2
from . import promocode_pb2_grpc

# Import application modules
from . import crud, models, schemas
from .database import SessionLocal
from .config import settings
from .models import DiscountTypeEnum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def _get_owner_id_from_context(context) -> uuid.UUID | None:
    """Extracts owner_id (as UUID) from gRPC metadata."""
    metadata = dict(context.invocation_metadata())
    owner_id_str = metadata.get('x-user-id') # Assuming gateway sets this header
    if not owner_id_str:
        logger.warning("Missing 'x-user-id' in metadata")
        context.abort(grpc.StatusCode.UNAUTHENTICATED, "User ID not found in request metadata")
        return None
    try:
        return uuid.UUID(owner_id_str)
    except ValueError:
        logger.warning(f"Invalid UUID format for owner_id: {owner_id_str}")
        context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid User ID format")
        return None

def _convert_db_promocode_to_proto(db_promocode: models.Promocode) -> promocode_pb2.Promocode:
    """Converts SQLAlchemy Promocode model to gRPC Promocode message."""
    proto_promocode = promocode_pb2.Promocode(
        id=str(db_promocode.id),
        code=db_promocode.code,
        # Map Enum correctly - gRPC uses enum number, proto definition maps names
        discount_type=promocode_pb2.DiscountType.Value(db_promocode.discount_type.name),
        discount_value=db_promocode.discount_value,
        usage_limit=db_promocode.usage_limit,
        usage_count=db_promocode.usage_count,
        owner_id=str(db_promocode.owner_id),
        is_active=db_promocode.is_active,
    )
    # Handle optional Timestamps
    if db_promocode.expiration_date:
        ts = Timestamp()
        ts.FromDatetime(db_promocode.expiration_date)
        proto_promocode.expiration_date.CopyFrom(ts)
    if db_promocode.created_at:
        ts_created = Timestamp()
        ts_created.FromDatetime(db_promocode.created_at)
        proto_promocode.created_at.CopyFrom(ts_created)
    if db_promocode.updated_at:
        ts_updated = Timestamp()
        ts_updated.FromDatetime(db_promocode.updated_at)
        proto_promocode.updated_at.CopyFrom(ts_updated)

    return proto_promocode

# --- Servicer Implementation ---

class PromocodeServiceServicer(promocode_pb2_grpc.PromocodeServiceServicer):
    """Provides methods that implement functionality of promocode server."""

    def CreatePromocode(self, request: promocode_pb2.CreatePromocodeRequest, context):
        logger.info(f"Received CreatePromocode request for code: {request.code}")
        owner_id = _get_owner_id_from_context(context)
        if not owner_id:
            return promocode_pb2.PromocodeResponse() # Abort called in helper

        db = SessionLocal()
        try:
            # Check for duplicate code
            existing_code = crud.get_promocode_by_code(db, code=request.code)
            if existing_code:
                logger.warning(f"Attempted to create duplicate promocode code: {request.code}")
                context.abort(grpc.StatusCode.ALREADY_EXISTS, f"Promocode with code '{request.code}' already exists.")
                return promocode_pb2.PromocodeResponse()

            # Convert gRPC enum to model enum
            try:
                discount_type_enum = DiscountTypeEnum[promocode_pb2.DiscountType.Name(request.discount_type)]
            except KeyError:
                 logger.warning(f"Invalid DiscountType received: {request.discount_type}")
                 context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid discount type provided.")
                 return promocode_pb2.PromocodeResponse()

            # Convert expiration date from Timestamp to datetime if present
            expiration_date_dt = None
            if request.HasField('expiration_date'):
                expiration_date_dt = request.expiration_date.ToDatetime()

            # Validate with Pydantic schema
            promocode_data = schemas.PromocodeCreate(
                code=request.code,
                discount_type=discount_type_enum,
                discount_value=request.discount_value,
                expiration_date=expiration_date_dt,
                usage_limit=request.usage_limit,
                # is_active is True by default in schema
            )

            db_promocode = crud.create_promocode(db=db, promocode=promocode_data, owner_id=owner_id)
            logger.info(f"Successfully created promocode ID: {db_promocode.id}")
            proto_promocode = _convert_db_promocode_to_proto(db_promocode)
            return promocode_pb2.PromocodeResponse(promocode=proto_promocode)

        except Exception as e:
            logger.error(f"Error creating promocode: {e}", exc_info=True)
            context.abort(grpc.StatusCode.INTERNAL, "Internal server error creating promocode.")
            return promocode_pb2.PromocodeResponse()
        finally:
            db.close()

    def GetPromocode(self, request: promocode_pb2.GetPromocodeRequest, context):
        logger.info(f"Received GetPromocode request for ID: {request.id}")
        owner_id = _get_owner_id_from_context(context)
        if not owner_id:
            return promocode_pb2.PromocodeResponse()

        try:
            promocode_id = uuid.UUID(request.id)
        except ValueError:
            logger.warning(f"Invalid UUID format for GetPromocode ID: {request.id}")
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid Promocode ID format.")
            return promocode_pb2.PromocodeResponse()

        db = SessionLocal()
        try:
            db_promocode = crud.get_promocode_by_id(db=db, promocode_id=promocode_id, owner_id=owner_id)
            if db_promocode is None:
                logger.warning(f"Promocode not found for ID: {request.id} and owner: {owner_id}")
                context.abort(grpc.StatusCode.NOT_FOUND, "Promocode not found.")
                return promocode_pb2.PromocodeResponse()

            logger.info(f"Successfully retrieved promocode ID: {db_promocode.id}")
            proto_promocode = _convert_db_promocode_to_proto(db_promocode)
            return promocode_pb2.PromocodeResponse(promocode=proto_promocode)
        except Exception as e:
            logger.error(f"Error getting promocode {request.id}: {e}", exc_info=True)
            context.abort(grpc.StatusCode.INTERNAL, "Internal server error getting promocode.")
            return promocode_pb2.PromocodeResponse()
        finally:
            db.close()

    def ListPromocodes(self, request: promocode_pb2.ListPromocodesRequest, context):
        logger.info(f"Received ListPromocodes request for page: {request.page}, size: {request.page_size}")
        owner_id = _get_owner_id_from_context(context)
        if not owner_id:
            return promocode_pb2.ListPromocodesResponse()

        page = request.page if request.page > 0 else 1
        page_size = request.page_size if request.page_size > 0 else 10 # Default page size
        skip = (page - 1) * page_size

        db = SessionLocal()
        try:
            db_promocodes, total_count = crud.get_promocodes_by_owner(
                db=db, owner_id=owner_id, skip=skip, limit=page_size
            )

            proto_promocodes = [_convert_db_promocode_to_proto(p) for p in db_promocodes]

            logger.info(f"Successfully listed {len(proto_promocodes)} promocodes for owner {owner_id}")
            return promocode_pb2.ListPromocodesResponse(
                promocodes=proto_promocodes,
                total_count=total_count,
                page=page,
                page_size=page_size
            )
        except Exception as e:
            logger.error(f"Error listing promocodes for owner {owner_id}: {e}", exc_info=True)
            context.abort(grpc.StatusCode.INTERNAL, "Internal server error listing promocodes.")
            return promocode_pb2.ListPromocodesResponse()
        finally:
            db.close()

    def UpdatePromocode(self, request: promocode_pb2.UpdatePromocodeRequest, context):
        logger.info(f"Received UpdatePromocode request for ID: {request.id}")
        owner_id = _get_owner_id_from_context(context)
        if not owner_id:
            return promocode_pb2.PromocodeResponse()

        try:
            promocode_id = uuid.UUID(request.id)
        except ValueError:
            logger.warning(f"Invalid UUID format for UpdatePromocode ID: {request.id}")
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid Promocode ID format.")
            return promocode_pb2.PromocodeResponse()

        db = SessionLocal()
        try:
            # Prepare update data using Pydantic model for validation and structure
            update_data = {}
            if request.HasField('code'):
                update_data['code'] = request.code
            if request.HasField('discount_type'):
                 try:
                     update_data['discount_type'] = DiscountTypeEnum[promocode_pb2.DiscountType.Name(request.discount_type)]
                 except KeyError:
                     logger.warning(f"Invalid DiscountType received for update: {request.discount_type}")
                     context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid discount type provided.")
                     return promocode_pb2.PromocodeResponse()
            if request.HasField('discount_value'):
                update_data['discount_value'] = request.discount_value
            if request.HasField('expiration_date'):
                update_data['expiration_date'] = request.expiration_date.ToDatetime()
            if request.HasField('usage_limit'):
                update_data['usage_limit'] = request.usage_limit
            if request.HasField('is_active'):
                update_data['is_active'] = request.is_active

            if not update_data:
                 context.abort(grpc.StatusCode.INVALID_ARGUMENT, "No update fields provided.")
                 return promocode_pb2.PromocodeResponse()

            promocode_update_schema = schemas.PromocodeUpdate(**update_data)

            # Check for code uniqueness if code is being updated
            if 'code' in update_data:
                 existing_code = crud.get_promocode_by_code(db, update_data['code'])
                 # Ensure the found code doesn't belong to the promocode we are updating
                 if existing_code and existing_code.id != promocode_id:
                     logger.warning(f"Attempted to update promocode {request.id} with duplicate code: {update_data['code']}")
                     context.abort(grpc.StatusCode.ALREADY_EXISTS, f"Promocode with code '{update_data['code']}' already exists.")
                     return promocode_pb2.PromocodeResponse()


            updated_promocode = crud.update_promocode(
                db=db,
                promocode_id=promocode_id,
                promocode_update=promocode_update_schema,
                owner_id=owner_id
            )

            if updated_promocode is None:
                # Could be Not Found or Code Conflict (handled above, but double check)
                # Check if the promocode actually exists for this owner first
                exists = crud.get_promocode_by_id(db, promocode_id, owner_id)
                if not exists:
                    logger.warning(f"Promocode not found for update: ID {request.id}, owner {owner_id}")
                    context.abort(grpc.StatusCode.NOT_FOUND, "Promocode not found.")
                else:
                    # This case should ideally be caught by the code uniqueness check above
                    logger.error(f"Update failed for promocode {request.id}, possibly due to unforeseen conflict.")
                    context.abort(grpc.StatusCode.INTERNAL, "Failed to update promocode.")
                return promocode_pb2.PromocodeResponse()

            logger.info(f"Successfully updated promocode ID: {updated_promocode.id}")
            proto_promocode = _convert_db_promocode_to_proto(updated_promocode)
            return promocode_pb2.PromocodeResponse(promocode=proto_promocode)

        except Exception as e:
            logger.error(f"Error updating promocode {request.id}: {e}", exc_info=True)
            context.abort(grpc.StatusCode.INTERNAL, "Internal server error updating promocode.")
            return promocode_pb2.PromocodeResponse()
        finally:
            db.close()

    def DeletePromocode(self, request: promocode_pb2.DeletePromocodeRequest, context):
        logger.info(f"Received DeletePromocode request for ID: {request.id}")
        owner_id = _get_owner_id_from_context(context)
        if not owner_id:
            return Empty() # Abort called in helper

        try:
            promocode_id = uuid.UUID(request.id)
        except ValueError:
            logger.warning(f"Invalid UUID format for DeletePromocode ID: {request.id}")
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid Promocode ID format.")
            return Empty()

        db = SessionLocal()
        try:
            deleted = crud.delete_promocode(db=db, promocode_id=promocode_id, owner_id=owner_id)

            if not deleted:
                logger.warning(f"Promocode not found for deletion: ID {request.id}, owner {owner_id}")
                context.abort(grpc.StatusCode.NOT_FOUND, "Promocode not found.")
                return Empty()

            logger.info(f"Successfully deleted promocode ID: {request.id}")
            return Empty()
        except Exception as e:
            logger.error(f"Error deleting promocode {request.id}: {e}", exc_info=True)
            context.abort(grpc.StatusCode.INTERNAL, "Internal server error deleting promocode.")
            return Empty()
        finally:
            db.close()

# --- Server Setup ---

def serve():
    """Starts the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    promocode_pb2_grpc.add_PromocodeServiceServicer_to_server(
        PromocodeServiceServicer(), server
    )
    grpc_port = settings.GRPC_PORT
    server_address = f'[::]:{grpc_port}'
    server.add_insecure_port(server_address) # Use add_secure_port in production with credentials
    logger.info(f"Starting gRPC server on {server_address}")
    server.start()
    logger.info("gRPC server started successfully.")
    server.wait_for_termination()

# Note: This file defines the server logic.
# You'll need a main.py to call serve()
