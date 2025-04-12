import grpc
import logging
from contextlib import contextmanager
from app.config import settings
from app import promocode_pb2_grpc  # Import generated stub

logger = logging.getLogger(__name__)

_channel = grpc.insecure_channel(settings.PROMOCODE_SERVICE_GRPC_URL)
_promocode_stub = promocode_pb2_grpc.PromocodeServiceStub(_channel)


def get_promocode_stub() -> promocode_pb2_grpc.PromocodeServiceStub:
    """Returns the gRPC stub for the Promocode service."""
    return _promocode_stub


@contextmanager
def promocode_service_stub():
    """Context manager to provide the promocode service stub."""
    try:
        yield _promocode_stub
    except grpc.RpcError as e:
        logger.error(f"gRPC call failed: {e.code()} - {e.details()}")
        raise e
    # except Exception as e:
    #     logger.error(f"An unexpected error occurred during gRPC call: {e}")
    #     raise e # Re-raise generic exceptions
