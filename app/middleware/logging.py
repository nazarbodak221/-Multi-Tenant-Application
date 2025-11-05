"""
Structured logging middleware
Provides request/response logging with structured data
"""
import time
import logging
import json
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.tenant_manager import TenantContext

logger = logging.getLogger(__name__)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request/response logging
    Logs request details, response status, timing, and tenant context
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response with structured data
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response from route handler
        """
        start_time = time.time()
        
        # Extract request information
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        tenant_id = TenantContext.get_tenant()
        
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Build request log data
        request_log_data = {
            "event": "request",
            "method": method,
            "path": path,
            "query_params": query_params,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "tenant_id": tenant_id,
        }
        
        # Log request
        logger.info(
            f"{method} {path}",
            extra=request_log_data
        )
        
        try:
            response = await call_next(request)

            duration = time.time() - start_time
            
            status_code = response.status_code
            
            response_log_data = {
                "event": "response",
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration * 1000, 2),
                "tenant_id": tenant_id,
            }
            
            # Log response
            log_level = logging.INFO
            if status_code >= 500:
                log_level = logging.ERROR
            elif status_code >= 400:
                log_level = logging.WARNING
            
            logger.log(
                log_level,
                f"{method} {path} {status_code} ({round(duration * 1000, 2)}ms)",
                extra=response_log_data
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                f"{method} {path} - Exception: {str(e)}",
                exc_info=True,
                extra={
                    "event": "error",
                    "method": method,
                    "path": path,
                    "duration_ms": round(duration * 1000, 2),
                    "tenant_id": tenant_id,
                    "error": str(e),
                }
            )
            
            raise


def setup_logging(level: str = "INFO"):
    """
    Setup structured logging configuration
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    import sys
    
    # Configure logging format
    log_format = json.dumps({
        "timestamp": "%(asctime)s",
        "level": "%(levelname)s",
        "logger": "%(name)s",
        "message": "%(message)s",
        "extra": "%(extra)s" if hasattr(logging, 'extra') else None,
    })
    
    # Simple format for console
    simple_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=simple_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # Set specific log levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    logger.info(f"Logging configured with level: {level}")

