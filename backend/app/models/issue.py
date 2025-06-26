from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class IssueType(str, Enum):
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    IMPROVEMENT = "improvement"
    AUTO_ERROR = "auto_error"
    PERFORMANCE = "performance"

class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class IssueStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class IssuePriority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class UserInfo(BaseModel):
    user_id: str
    username: str
    role: str
    email: Optional[str] = None

class UserContext(BaseModel):
    page: Optional[str] = None
    browser: Optional[str] = None
    user_agent: Optional[str] = None
    actions: Optional[List[str]] = []
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorDetails(BaseModel):
    error_message: str
    stack_trace: Optional[str] = None
    error_type: Optional[str] = None
    request_info: Optional[Dict[str, Any]] = {}

class PerformanceData(BaseModel):
    load_time: Optional[int] = None  # milliseconds
    endpoint: Optional[str] = None
    response_time: Optional[int] = None  # milliseconds
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None

class IssueCreate(BaseModel):
    type: IssueType
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    severity: IssueSeverity = IssueSeverity.MEDIUM
    priority: IssuePriority = IssuePriority.MEDIUM
    context: Optional[UserContext] = None
    tags: Optional[List[str]] = []
    attachments: Optional[List[str]] = []  # URLs to screenshots/files

class AutoErrorCreate(BaseModel):
    title: str
    error_details: ErrorDetails
    user_info: UserInfo
    context: UserContext
    severity: IssueSeverity = IssueSeverity.HIGH
    tags: Optional[List[str]] = []

class PerformanceIssueCreate(BaseModel):
    title: str
    description: str
    performance_data: PerformanceData
    user_info: UserInfo
    context: UserContext
    severity: IssueSeverity = IssueSeverity.LOW

class IssueResponse(BaseModel):
    id: str
    type: IssueType
    title: str
    description: str
    severity: IssueSeverity
    priority: IssuePriority
    status: IssueStatus
    user_info: UserInfo
    context: Optional[UserContext] = None
    error_details: Optional[ErrorDetails] = None
    performance_data: Optional[PerformanceData] = None
    tags: List[str] = []
    attachments: List[str] = []
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    jira_ticket_id: Optional[str] = None  # For future Jira integration

class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[IssueSeverity] = None
    priority: Optional[IssuePriority] = None
    status: Optional[IssueStatus] = None
    tags: Optional[List[str]] = None
    resolution_notes: Optional[str] = None

class IssueFilters(BaseModel):
    type: Optional[IssueType] = None
    severity: Optional[IssueSeverity] = None
    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
    user_id: Optional[str] = None
    tags: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None