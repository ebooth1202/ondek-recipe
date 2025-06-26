from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
import logging

from ..database import db
from ..models.issue import (
    IssueCreate, IssueResponse, IssueUpdate, IssueFilters,
    AutoErrorCreate, PerformanceIssueCreate, UserInfo, UserContext,
    IssueType, IssueSeverity, IssueStatus, IssuePriority
)
from ..middleware.auth import get_current_user, require_role
from ..models.user import UserRole
from ..utils.email_service import email_service

router = APIRouter(prefix="/issues", tags=["issue-tracking"])
logger = logging.getLogger(__name__)


def get_user_info(current_user: dict) -> UserInfo:
    """Extract user info from current user context"""
    return UserInfo(
        user_id=str(current_user["_id"]),
        username=current_user["username"],
        role=current_user["role"],
        email=current_user.get("email")
    )


def get_user_context(request: Request) -> UserContext:
    """Extract user context from request"""
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
        browser=browser,
        user_agent=user_agent,
        timestamp=datetime.now()
    )


@router.post("/report", response_model=IssueResponse)
async def create_user_report(
        issue: IssueCreate,
        request: Request,
        current_user: dict = Depends(get_current_user)
):
    """Create a new user-reported issue (bug, feature request, improvement)"""
    try:
        user_info = get_user_info(current_user)
        context = get_user_context(request)

        # Merge user-provided context with extracted context
        if issue.context:
            context.page = issue.context.page or context.page
            context.actions = issue.context.actions or context.actions

        issue_doc = {
            "type": issue.type.value,
            "title": issue.title,
            "description": issue.description,
            "severity": issue.severity.value,
            "priority": issue.priority.value,
            "status": IssueStatus.OPEN.value,
            "user_info": user_info.dict(),
            "context": context.dict(),
            "tags": issue.tags or [],
            "attachments": issue.attachments or [],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "resolved_at": None,
            "resolution_notes": None,
            "jira_ticket_id": None
        }

        result = db.issues.insert_one(issue_doc)
        issue_doc["id"] = str(result.inserted_id)

        # Send email notification for high/critical issues or feature requests
        if (issue.severity in [IssueSeverity.HIGH, IssueSeverity.CRITICAL] or
                issue.type == IssueType.FEATURE_REQUEST):

            email_data = {
                "type": issue.type.value,
                "title": issue.title,
                "description": issue.description,
                "severity": issue.severity.value,
                "username": user_info.username,
                "user_role": user_info.role,
                "page": context.page,
                "created_at": issue_doc["created_at"].strftime('%Y-%m-%d %H:%M:%S'),
                "tags": issue.tags
            }

            try:
                email_service.send_new_user_report_notification(email_data)
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")
                # Don't fail the request if email fails

        logger.info(f"New {issue.type.value} reported by {user_info.username}: {issue.title}")

        return IssueResponse(
            id=str(result.inserted_id),
            type=issue.type,
            title=issue.title,
            description=issue.description,
            severity=issue.severity,
            priority=issue.priority,
            status=IssueStatus.OPEN,
            user_info=user_info,
            context=context,
            tags=issue.tags or [],
            attachments=issue.attachments or [],
            created_at=issue_doc["created_at"],
            updated_at=issue_doc["updated_at"]
        )

    except Exception as e:
        logger.error(f"Error creating user report: {e}")
        raise HTTPException(status_code=500, detail="Failed to create issue report")


@router.post("/auto-error", response_model=IssueResponse)
async def create_auto_error(auto_error: AutoErrorCreate):
    """Create an automatically detected error issue (internal use)"""
    try:
        issue_doc = {
            "type": IssueType.AUTO_ERROR.value,
            "title": auto_error.title,
            "description": f"Automatic error detection: {auto_error.error_details.error_message}",
            "severity": auto_error.severity.value,
            "priority": IssuePriority.HIGH.value if auto_error.severity == IssueSeverity.CRITICAL else IssuePriority.MEDIUM.value,
            "status": IssueStatus.OPEN.value,
            "user_info": auto_error.user_info.dict(),
            "context": auto_error.context.dict(),
            "error_details": auto_error.error_details.dict(),
            "tags": auto_error.tags or ["auto-detected", "error"],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "resolved_at": None,
            "resolution_notes": None,
            "jira_ticket_id": None
        }

        result = db.issues.insert_one(issue_doc)

        # Send critical error email
        if auto_error.severity == IssueSeverity.CRITICAL:
            email_data = {
                "error_message": auto_error.error_details.error_message,
                "stack_trace": auto_error.error_details.stack_trace,
                "username": auto_error.user_info.username,
                "user_role": auto_error.user_info.role,
                "page": auto_error.context.page,
                "endpoint": auto_error.error_details.request_info.get("endpoint"),
                "timestamp": auto_error.context.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }

            try:
                email_service.send_critical_error_alert(email_data)
            except Exception as e:
                logger.error(f"Failed to send critical error email: {e}")

        logger.error(f"Auto-detected {auto_error.severity.value} error: {auto_error.title}")

        return IssueResponse(
            id=str(result.inserted_id),
            type=IssueType.AUTO_ERROR,
            title=auto_error.title,
            description=issue_doc["description"],
            severity=auto_error.severity,
            priority=IssuePriority(issue_doc["priority"]),
            status=IssueStatus.OPEN,
            user_info=auto_error.user_info,
            context=auto_error.context,
            error_details=auto_error.error_details,
            tags=issue_doc["tags"],
            created_at=issue_doc["created_at"],
            updated_at=issue_doc["updated_at"]
        )

    except Exception as e:
        logger.error(f"Error creating auto error report: {e}")
        raise HTTPException(status_code=500, detail="Failed to create auto error report")


@router.post("/performance", response_model=IssueResponse)
async def create_performance_issue(perf_issue: PerformanceIssueCreate):
    """Create a performance issue report"""
    try:
        issue_doc = {
            "type": IssueType.PERFORMANCE.value,
            "title": perf_issue.title,
            "description": perf_issue.description,
            "severity": perf_issue.severity.value,
            "priority": IssuePriority.LOW.value,
            "status": IssueStatus.OPEN.value,
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

        result = db.issues.insert_one(issue_doc)

        logger.info(f"Performance issue logged: {perf_issue.title}")

        return IssueResponse(
            id=str(result.inserted_id),
            type=IssueType.PERFORMANCE,
            title=perf_issue.title,
            description=perf_issue.description,
            severity=perf_issue.severity,
            priority=IssuePriority.LOW,
            status=IssueStatus.OPEN,
            user_info=perf_issue.user_info,
            context=perf_issue.context,
            performance_data=perf_issue.performance_data,
            tags=issue_doc["tags"],
            created_at=issue_doc["created_at"],
            updated_at=issue_doc["updated_at"]
        )

    except Exception as e:
        logger.error(f"Error creating performance issue: {e}")
        raise HTTPException(status_code=500, detail="Failed to create performance issue")


@router.get("/", response_model=List[IssueResponse])
async def get_issues(
        type: Optional[IssueType] = Query(None, description="Filter by issue type"),
        severity: Optional[IssueSeverity] = Query(None, description="Filter by severity"),
        status: Optional[IssueStatus] = Query(None, description="Filter by status"),
        priority: Optional[IssuePriority] = Query(None, description="Filter by priority"),
        skip: int = Query(0, ge=0, description="Number of issues to skip"),
        limit: int = Query(50, ge=1, le=100, description="Number of issues to return"),
        current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.OWNER]))
):
    """Get issues with filtering - Admin/Owner only"""
    try:
        query = {}

        if type:
            query["type"] = type.value
        if severity:
            query["severity"] = severity.value
        if status:
            query["status"] = status.value
        if priority:
            query["priority"] = priority.value

        cursor = db.issues.find(query).skip(skip).limit(limit).sort("created_at", -1)
        issues = []

        for issue_doc in cursor:
            issues.append(_build_issue_response(issue_doc))

        return issues

    except Exception as e:
        logger.error(f"Error retrieving issues: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve issues")


@router.get("/my-reports", response_model=List[IssueResponse])
async def get_my_reports(
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=50),
        current_user: dict = Depends(get_current_user)
):
    """Get current user's reported issues"""
    try:
        query = {"user_info.user_id": str(current_user["_id"])}

        cursor = db.issues.find(query).skip(skip).limit(limit).sort("created_at", -1)
        issues = []

        for issue_doc in cursor:
            issues.append(_build_issue_response(issue_doc))

        return issues

    except Exception as e:
        logger.error(f"Error retrieving user reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve your reports")


@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue(
        issue_id: str,
        current_user: dict = Depends(get_current_user)
):
    """Get a specific issue by ID"""
    try:
        if not ObjectId.is_valid(issue_id):
            raise HTTPException(status_code=400, detail="Invalid issue ID")

        issue_doc = db.issues.find_one({"_id": ObjectId(issue_id)})
        if not issue_doc:
            raise HTTPException(status_code=404, detail="Issue not found")

        # Check permissions: user can see their own issues, admins can see all
        if (current_user["role"] not in ["admin", "owner"] and
                issue_doc["user_info"]["user_id"] != str(current_user["_id"])):
            raise HTTPException(status_code=403, detail="Not authorized to view this issue")

        return _build_issue_response(issue_doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving issue: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve issue")


@router.put("/{issue_id}", response_model=IssueResponse)
async def update_issue(
        issue_id: str,
        issue_update: IssueUpdate,
        current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.OWNER]))
):
    """Update an issue - Admin/Owner only"""
    try:
        if not ObjectId.is_valid(issue_id):
            raise HTTPException(status_code=400, detail="Invalid issue ID")

        existing_issue = db.issues.find_one({"_id": ObjectId(issue_id)})
        if not existing_issue:
            raise HTTPException(status_code=404, detail="Issue not found")

        update_doc = {"updated_at": datetime.now()}

        if issue_update.title is not None:
            update_doc["title"] = issue_update.title
        if issue_update.description is not None:
            update_doc["description"] = issue_update.description
        if issue_update.severity is not None:
            update_doc["severity"] = issue_update.severity.value
        if issue_update.priority is not None:
            update_doc["priority"] = issue_update.priority.value
        if issue_update.status is not None:
            update_doc["status"] = issue_update.status.value
            if issue_update.status in [IssueStatus.RESOLVED, IssueStatus.CLOSED]:
                update_doc["resolved_at"] = datetime.now()
        if issue_update.tags is not None:
            update_doc["tags"] = issue_update.tags
        if issue_update.resolution_notes is not None:
            update_doc["resolution_notes"] = issue_update.resolution_notes

        result = db.issues.update_one(
            {"_id": ObjectId(issue_id)},
            {"$set": update_doc}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes were made")

        updated_issue = db.issues.find_one({"_id": ObjectId(issue_id)})
        return _build_issue_response(updated_issue)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating issue: {e}")
        raise HTTPException(status_code=500, detail="Failed to update issue")


@router.delete("/{issue_id}")
async def delete_issue(
        issue_id: str,
        current_user: dict = Depends(require_role([UserRole.OWNER]))  # Only owners can delete
):
    """Delete an issue - Owner only"""
    try:
        if not ObjectId.is_valid(issue_id):
            raise HTTPException(status_code=400, detail="Invalid issue ID")

        result = db.issues.delete_one({"_id": ObjectId(issue_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Issue not found")

        return {"message": "Issue deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting issue: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete issue")


@router.get("/stats/summary")
async def get_issue_statistics(
        current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.OWNER]))
):
    """Get issue statistics - Admin/Owner only"""
    try:
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "type": "$type",
                        "severity": "$severity",
                        "status": "$status"
                    },
                    "count": {"$sum": 1}
                }
            }
        ]

        result = list(db.issues.aggregate(pipeline))

        stats = {
            "total_issues": 0,
            "by_type": {},
            "by_severity": {},
            "by_status": {},
            "open_critical": 0,
            "open_high": 0
        }

        for item in result:
            stats["total_issues"] += item["count"]

            # Count by type
            issue_type = item["_id"]["type"]
            stats["by_type"][issue_type] = stats["by_type"].get(issue_type, 0) + item["count"]

            # Count by severity
            severity = item["_id"]["severity"]
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + item["count"]

            # Count by status
            status = item["_id"]["status"]
            stats["by_status"][status] = stats["by_status"].get(status, 0) + item["count"]

            # Count open critical/high issues
            if item["_id"]["status"] == "open":
                if item["_id"]["severity"] == "critical":
                    stats["open_critical"] += item["count"]
                elif item["_id"]["severity"] == "high":
                    stats["open_high"] += item["count"]

        return stats

    except Exception as e:
        logger.error(f"Error getting issue statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get issue statistics")


def _build_issue_response(issue_doc: dict) -> IssueResponse:
    """Helper function to build IssueResponse from database document"""
    return IssueResponse(
        id=str(issue_doc["_id"]),
        type=IssueType(issue_doc["type"]),
        title=issue_doc["title"],
        description=issue_doc["description"],
        severity=IssueSeverity(issue_doc["severity"]),
        priority=IssuePriority(issue_doc["priority"]),
        status=IssueStatus(issue_doc["status"]),
        user_info=UserInfo(**issue_doc["user_info"]),
        context=UserContext(**issue_doc["context"]) if issue_doc.get("context") else None,
        error_details=issue_doc.get("error_details"),
        performance_data=issue_doc.get("performance_data"),
        tags=issue_doc.get("tags", []),
        attachments=issue_doc.get("attachments", []),
        resolution_notes=issue_doc.get("resolution_notes"),
        created_at=issue_doc["created_at"],
        updated_at=issue_doc["updated_at"],
        resolved_at=issue_doc.get("resolved_at"),
        jira_ticket_id=issue_doc.get("jira_ticket_id")
    )