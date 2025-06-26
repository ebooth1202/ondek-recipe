import traceback
import logging
import time
from datetime import datetime
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..database import db
from ..models.issue import AutoErrorCreate, ErrorDetails, UserInfo, UserContext, IssueSeverity
from ..utils.email_service import email_service

logger = logging.getLogger(__name__)


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, track_performance: bool = True):
        super().__init__(app)
        self.track_performance = track_performance
        self.performance_threshold = 5000  # 5 seconds

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = None
        error_occurred = False

        try:
            response = await call_next(request)
            return response

        except HTTPException as e:
            # Handle known HTTP exceptions (don't log these as critical errors)
            if e.status_code >= 500:
                await self._log_error(
                    request=request,
                    error=e,
                    severity=IssueSeverity.HIGH if e.status_code >= 500 else IssueSeverity.MEDIUM
                )
            error_occurred = True
            raise

        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unhandled error: {str(e)}")
            error_occurred = True

            await self._log_error(
                request=request,
                error=e,
                severity=IssueSeverity.CRITICAL
            )

            # Return a generic error response
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error. The issue has been logged and will be investigated."}
            )

        finally:
            # Log performance issues if enabled
            if self.track_performance and not error_occurred and response:
                processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

                if processing_time > self.performance_threshold:
                    await self._log_performance_issue(
                        request=request,
                        response=response,
                        processing_time=processing_time
                    )

    async def _log_error(self, request: Request, error: Exception, severity: IssueSeverity):
        """Log error to database and send email if critical"""
        try:
            # Extract user information
            user_info = await self._get_user_info(request)

            # Extract request context
            context = self._get_request_context(request)

            # Create error details
            error_details = ErrorDetails(
                error_message=str(error),
                stack_trace=traceback.format_exc(),
                error_type=type(error).__name__,
                request_info={
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers),
                    "query_params": dict(request.query_params)
                }
            )

            # Create auto error report
            auto_error = AutoErrorCreate(
                title=f"{type(error).__name__}: {str(error)[:100]}",
                error_details=error_details,
                user_info=user_info,
                context=context,
                severity=severity,
                tags=["auto-detected", "backend", type(error).__name__.lower()]
            )

            # Save to database
            if db is not None:
                issue_doc = {
                    "type": "auto_error",
                    "title": auto_error.title,
                    "description": f"Automatic error detection: {auto_error.error_details.error_message}",
                    "severity": auto_error.severity.value,
                    "priority": "high" if auto_error.severity == IssueSeverity.CRITICAL else "medium",
                    "status": "open",
                    "user_info": auto_error.user_info.dict(),
                    "context": auto_error.context.dict(),
                    "error_details": auto_error.error_details.dict(),
                    "tags": auto_error.tags,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "resolved_at": None,
                    "resolution_notes": None,
                    "jira_ticket_id": None
                }

                db.issues.insert_one(issue_doc)
                logger.info(f"Auto error logged: {auto_error.title}")

                # Send critical error email
                if severity == IssueSeverity.CRITICAL:
                    email_data = {
                        "error_message": auto_error.error_details.error_message,
                        "stack_trace": auto_error.error_details.stack_trace,
                        "username": auto_error.user_info.username,
                        "user_role": auto_error.user_info.role,
                        "page": auto_error.context.page,
                        "endpoint": f"{request.method} {request.url.path}",
                        "timestamp": auto_error.context.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    }

                    try:
                        email_service.send_critical_error_alert(email_data)
                    except Exception as e:
                        logger.error(f"Failed to send critical error email: {e}")

        except Exception as e:
            logger.error(f"Failed to log error to database: {e}")

    async def _log_performance_issue(self, request: Request, response: Response, processing_time: float):
        """Log performance issues"""
        try:
            from ..models.issue import PerformanceIssueCreate, PerformanceData

            user_info = await self._get_user_info(request)
            context = self._get_request_context(request)

            performance_data = PerformanceData(
                response_time=int(processing_time),
                endpoint=f"{request.method} {request.url.path}",
                load_time=int(processing_time)
            )

            perf_issue = PerformanceIssueCreate(
                title=f"Slow response: {request.method} {request.url.path}",
                description=f"Endpoint took {processing_time:.2f}ms to respond (threshold: {self.performance_threshold}ms)",
                performance_data=performance_data,
                user_info=user_info,
                context=context,
                severity=IssueSeverity.LOW
            )

            # Save to database
            if db is not None:
                issue_doc = {
                    "type": "performance",
                    "title": perf_issue.title,
                    "description": perf_issue.description,
                    "severity": perf_issue.severity.value,
                    "priority": "low",
                    "status": "open",
                    "user_info": perf_issue.user_info.dict(),
                    "context": perf_issue.context.dict(),
                    "performance_data": perf_issue.performance_data.dict(),
                    "tags": ["performance", "auto-detected"],
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "resolved_at": None,
                    "resolution_notes": None,
                    "jira_ticket_id": None
                }

                db.issues.insert_one(issue_doc)
                logger.info(f"Performance issue logged: {perf_issue.title}")

        except Exception as e:
            logger.error(f"Failed to log performance issue: {e}")

    async def _get_user_info(self, request: Request) -> UserInfo:
        """Extract user info from request"""
        try:
            # Try to get user from authorization header
            from ..middleware.auth import get_current_user_from_request

            user = await get_current_user_from_request(request)
            if user:
                return UserInfo(
                    user_id=str(user["_id"]),
                    username=user["username"],
                    role=user["role"],
                    email=user.get("email")
                )
        except:
            pass

        # Return anonymous user info
        return UserInfo(
            user_id="anonymous",
            username="anonymous",
            role="anonymous",
            email=None
        )

    def _get_request_context(self, request: Request) -> UserContext:
        """Extract request context"""
        user_agent = request.headers.get("user-agent", "")
        browser = "Unknown"

        # Simple browser detection
        if "Chrome" in user_agent:
            browser = "Chrome"
        elif "Firefox" in user_agent:
            browser = "Firefox"
        elif "Safari" in user_agent:
            browser = "Safari"
        elif "Edge" in user_agent:
            browser = "Edge"

        return UserContext(
            page=str(request.url.path),
            browser=browser,
            user_agent=user_agent,
            timestamp=datetime.now()
        )


# Helper function to get user from request without dependencies
async def get_current_user_from_request(request: Request) -> Optional[dict]:
    """Get current user from request without using Depends"""
    try:
        from jose import jwt
        from ..database import db
        import os

        SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")

        # Try to get token from Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None

        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return None
        except ValueError:
            return None

        # Decode token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            username = payload.get("sub")
            if not username:
                return None
        except jwt.PyJWTError:
            return None

        # Get user from database
        if db is not None:
            user = db.users.find_one({"username": username})
            return user

    except Exception as e:
        logger.error(f"Error getting user from request: {e}")

    return None