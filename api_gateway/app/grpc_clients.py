import grpc
import logging
from contextlib import contextmanager
from app.config import settings
from app import promocode_pb2_grpc # Import generated stub

logger = logging.getLogger(__name__)

# Global channel (consider managing lifecycle with app startup/shutdown events for robustness)
# Using insecure channel for now, switch to secure channel in production
_channel = grpc.insecure_channel(settings.PROMOCODE_SERVICE_GRPC_URL)
_promocode_stub = promocode_pb2_grpc.PromocodeServiceStub(_channel)

def get_promocode_stub() -> promocode_pb2_grpc.PromocodeServiceStub:
    """Returns the gRPC stub for the Promocode service."""
    # Basic check if channel is alive, gRPC handles reconnections mostly
    # More sophisticated health checking could be added here
    return _promocode_stub

@contextmanager
def promocode_service_stub():
    """Context manager to provide the promocode service stub."""
    # In a more complex scenario, this could manage channel creation/closing
    # For now, it just yields the globally created stub
    try:
        yield _promocode_stub
    except grpc.RpcError as e:
        logger.error(f"gRPC call failed: {e.code()} - {e.details()}")
        # Re-raise or handle specific errors
        raise e
    # except Exception as e:
    #     logger.error(f"An unexpected error occurred during gRPC call: {e}")
    #     raise e # Re-raise generic exceptions

# Optional: Add functions for graceful shutdown if needed
# async def close_grpc_channel():
#     global _channel
#     if _channel:
#         await _channel.close()
#         logger.info("gRPC channel closed.")
