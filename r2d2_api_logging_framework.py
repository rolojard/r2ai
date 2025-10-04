#!/usr/bin/env python3
"""
R2D2 API Logging Framework
==========================

Comprehensive logging framework for REST APIs, Flask applications,
and web service backends. Provides request/response tracking,
performance monitoring, and security event logging.

Features:
- Request/response logging with timing
- API endpoint performance monitoring
- Error tracking and correlation
- Security event detection
- Rate limiting and abuse detection
- Integration with Flask and other frameworks
- Structured JSON logging for agent analysis

Author: Expert Python Coder Agent
"""

import os
import sys
import time
import json
import logging
import functools
import threading
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from urllib.parse import urlparse, parse_qs
import uuid
from collections import defaultdict, deque

# Import our logging framework
sys.path.append('/home/rolo/r2ai')
from r2d2_logging_framework import R2D2LoggerFactory

@dataclass
class APIRequest:
    """Data class for API request tracking"""
    request_id: str
    method: str
    endpoint: str
    path: str
    query_params: Dict[str, Any]
    headers: Dict[str, str]
    remote_addr: str
    user_agent: str
    content_length: int
    timestamp: float
    auth_user: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class APIResponse:
    """Data class for API response tracking"""
    request_id: str
    status_code: int
    response_size: int
    processing_time: float
    error_message: Optional[str] = None
    cache_hit: bool = False

@dataclass
class SecurityEvent:
    """Data class for security events"""
    event_type: str
    severity: str
    remote_addr: str
    endpoint: str
    description: str
    timestamp: float
    user_agent: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

class APILoggingMiddleware:
    """
    Comprehensive API logging middleware for Flask and other frameworks
    """

    def __init__(self, service_name: str = "api_server", enable_security_monitoring: bool = True):
        """Initialize the API logging middleware"""
        self.service_name = service_name
        self.enable_security_monitoring = enable_security_monitoring

        # Create logging components
        self.logging_components = R2D2LoggerFactory.create_service_logger(
            service_name,
            enable_performance_monitoring=True,
            enable_websocket_logging=False,
            enable_vision_logging=False
        )

        self.logger = self.logging_components["logger"]
        self.perf_logger = self.logging_components["performance_logger"]

        # Request tracking
        self.active_requests = {}  # request_id -> APIRequest
        self.request_history = deque(maxlen=1000)  # Recent requests
        self.security_events = deque(maxlen=500)   # Security events

        # Performance metrics
        self.endpoint_metrics = defaultdict(lambda: {
            "total_requests": 0,
            "total_time": 0.0,
            "error_count": 0,
            "success_count": 0,
            "min_time": float('inf'),
            "max_time": 0.0,
            "status_codes": defaultdict(int)
        })

        # Rate limiting tracking
        self.client_requests = defaultdict(lambda: deque(maxlen=100))  # IP -> timestamps
        self.rate_limit_violations = defaultdict(int)  # IP -> violation count

        # Thread safety
        self.lock = threading.Lock()

        self.logger.info("API logging middleware initialized", extra={
            "event_type": "api_middleware_initialized",
            "service": service_name,
            "security_monitoring": enable_security_monitoring
        })

    def create_request_id(self) -> str:
        """Generate unique request ID"""
        return f"req_{uuid.uuid4().hex[:12]}"

    def log_request_start(self, method: str, endpoint: str, path: str,
                         query_params: Dict[str, Any] = None,
                         headers: Dict[str, str] = None,
                         remote_addr: str = "unknown",
                         user_agent: str = "",
                         content_length: int = 0,
                         auth_user: str = None,
                         session_id: str = None) -> str:
        """
        Log the start of an API request

        Returns:
            request_id: Unique identifier for this request
        """
        request_id = self.create_request_id()
        timestamp = time.time()

        # Create request object
        api_request = APIRequest(
            request_id=request_id,
            method=method,
            endpoint=endpoint,
            path=path,
            query_params=query_params or {},
            headers=headers or {},
            remote_addr=remote_addr,
            user_agent=user_agent,
            content_length=content_length,
            timestamp=timestamp,
            auth_user=auth_user,
            session_id=session_id
        )

        # Store active request
        with self.lock:
            self.active_requests[request_id] = api_request

            # Track client requests for rate limiting
            if self.enable_security_monitoring:
                self.client_requests[remote_addr].append(timestamp)
                self._check_rate_limiting(remote_addr, endpoint)

        # Log request start
        self.logger.info(f"API request started: {method} {endpoint}", extra={
            "event_type": "api_request_start",
            "request_id": request_id,
            "method": method,
            "endpoint": endpoint,
            "path": path,
            "remote_addr": remote_addr,
            "user_agent": user_agent,
            "content_length": content_length,
            "auth_user": auth_user,
            "query_params": query_params,
            "active_requests": len(self.active_requests)
        })

        return request_id

    def log_request_end(self, request_id: str, status_code: int, response_size: int = 0,
                       error_message: str = None, cache_hit: bool = False):
        """
        Log the end of an API request

        Args:
            request_id: The request identifier
            status_code: HTTP status code
            response_size: Size of response in bytes
            error_message: Error message if request failed
            cache_hit: Whether response was served from cache
        """
        current_time = time.time()

        with self.lock:
            if request_id not in self.active_requests:
                self.logger.warning(f"Received response for unknown request: {request_id}", extra={
                    "event_type": "unknown_request_response",
                    "request_id": request_id
                })
                return

            api_request = self.active_requests.pop(request_id)

        # Calculate processing time
        processing_time = current_time - api_request.timestamp

        # Create response object
        api_response = APIResponse(
            request_id=request_id,
            status_code=status_code,
            response_size=response_size,
            processing_time=processing_time,
            error_message=error_message,
            cache_hit=cache_hit
        )

        # Add to history
        self.request_history.append((api_request, api_response))

        # Update endpoint metrics
        self._update_endpoint_metrics(api_request.endpoint, api_response)

        # Log request completion
        log_level = logging.ERROR if status_code >= 500 else (
            logging.WARNING if status_code >= 400 else logging.INFO
        )

        message = f"API request completed: {api_request.method} {api_request.endpoint} -> {status_code}"

        extra_data = {
            "event_type": "api_request_complete",
            "request_id": request_id,
            "method": api_request.method,
            "endpoint": api_request.endpoint,
            "status_code": status_code,
            "processing_time_seconds": round(processing_time, 4),
            "response_size_bytes": response_size,
            "remote_addr": api_request.remote_addr,
            "cache_hit": cache_hit
        }

        if error_message:
            extra_data["error_message"] = error_message

        if api_request.auth_user:
            extra_data["auth_user"] = api_request.auth_user

        self.logger.log(log_level, message, extra=extra_data)

        # Check for security events
        if self.enable_security_monitoring:
            self._check_security_events(api_request, api_response)

    def _update_endpoint_metrics(self, endpoint: str, response: APIResponse):
        """Update performance metrics for an endpoint"""
        metrics = self.endpoint_metrics[endpoint]

        metrics["total_requests"] += 1
        metrics["total_time"] += response.processing_time
        metrics["status_codes"][response.status_code] += 1

        if response.status_code >= 400:
            metrics["error_count"] += 1
        else:
            metrics["success_count"] += 1

        metrics["min_time"] = min(metrics["min_time"], response.processing_time)
        metrics["max_time"] = max(metrics["max_time"], response.processing_time)

    def _check_rate_limiting(self, remote_addr: str, endpoint: str):
        """Check for rate limiting violations"""
        current_time = time.time()
        client_requests = self.client_requests[remote_addr]

        # Count requests in last minute
        recent_requests = [t for t in client_requests if current_time - t < 60]

        # Rate limiting thresholds
        if len(recent_requests) > 100:  # More than 100 requests per minute
            self.rate_limit_violations[remote_addr] += 1
            self._log_security_event(
                "rate_limit_violation",
                "critical",
                remote_addr,
                endpoint,
                f"Rate limit exceeded: {len(recent_requests)} requests in last minute"
            )

    def _check_security_events(self, request: APIRequest, response: APIResponse):
        """Check for various security events"""
        # SQL injection attempts
        if self._detect_sql_injection(request):
            self._log_security_event(
                "sql_injection_attempt",
                "critical",
                request.remote_addr,
                request.endpoint,
                "Potential SQL injection detected in request parameters",
                request.user_agent,
                {"query_params": request.query_params}
            )

        # XSS attempts
        if self._detect_xss_attempt(request):
            self._log_security_event(
                "xss_attempt",
                "warning",
                request.remote_addr,
                request.endpoint,
                "Potential XSS attempt detected",
                request.user_agent
            )

        # Suspicious user agents
        if self._detect_suspicious_user_agent(request.user_agent):
            self._log_security_event(
                "suspicious_user_agent",
                "warning",
                request.remote_addr,
                request.endpoint,
                f"Suspicious user agent detected: {request.user_agent}",
                request.user_agent
            )

        # Failed authentication attempts
        if response.status_code == 401:
            self._log_security_event(
                "failed_authentication",
                "warning",
                request.remote_addr,
                request.endpoint,
                "Failed authentication attempt"
            )

        # Directory traversal attempts
        if self._detect_directory_traversal(request):
            self._log_security_event(
                "directory_traversal_attempt",
                "critical",
                request.remote_addr,
                request.endpoint,
                "Potential directory traversal attempt detected"
            )

    def _detect_sql_injection(self, request: APIRequest) -> bool:
        """Detect potential SQL injection attempts"""
        sql_patterns = [
            "union", "select", "insert", "update", "delete", "drop",
            "exec", "execute", "--", "/*", "*/", "xp_", "sp_",
            "0x", "char(", "cast(", "convert("
        ]

        # Check query parameters and path
        text_to_check = f"{request.path} {json.dumps(request.query_params)}".lower()

        return any(pattern in text_to_check for pattern in sql_patterns)

    def _detect_xss_attempt(self, request: APIRequest) -> bool:
        """Detect potential XSS attempts"""
        xss_patterns = [
            "<script", "javascript:", "onload=", "onerror=", "onclick=",
            "alert(", "document.cookie", "window.location"
        ]

        text_to_check = f"{request.path} {json.dumps(request.query_params)}".lower()

        return any(pattern in text_to_check for pattern in xss_patterns)

    def _detect_directory_traversal(self, request: APIRequest) -> bool:
        """Detect directory traversal attempts"""
        traversal_patterns = ["../", "..\\", "%2e%2e%2f", "%2e%2e\\"]

        return any(pattern in request.path.lower() for pattern in traversal_patterns)

    def _detect_suspicious_user_agent(self, user_agent: str) -> bool:
        """Detect suspicious user agents"""
        suspicious_patterns = [
            "sqlmap", "nikto", "nessus", "burp", "dirbuster",
            "gobuster", "wfuzz", "hydra", "nmap", "masscan"
        ]

        return any(pattern in user_agent.lower() for pattern in suspicious_patterns)

    def _log_security_event(self, event_type: str, severity: str, remote_addr: str,
                           endpoint: str, description: str, user_agent: str = None,
                           additional_data: Dict[str, Any] = None):
        """Log a security event"""
        timestamp = time.time()

        security_event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            remote_addr=remote_addr,
            endpoint=endpoint,
            description=description,
            timestamp=timestamp,
            user_agent=user_agent,
            additional_data=additional_data
        )

        self.security_events.append(security_event)

        # Log the security event
        log_level = getattr(logging, severity.upper(), logging.WARNING)
        message = f"Security event - {event_type}: {description}"

        extra_data = {
            "event_type": "security_event",
            "security_event_type": event_type,
            "severity": severity,
            "remote_addr": remote_addr,
            "endpoint": endpoint,
            "description": description
        }

        if user_agent:
            extra_data["user_agent"] = user_agent
        if additional_data:
            extra_data["additional_data"] = additional_data

        self.logger.log(log_level, message, extra=extra_data)

    def create_flask_middleware(self):
        """Create Flask middleware for automatic request/response logging"""
        def flask_logging_middleware(app):
            @app.before_request
            def before_request():
                from flask import request, g

                request_id = self.log_request_start(
                    method=request.method,
                    endpoint=request.endpoint or request.path,
                    path=request.path,
                    query_params=dict(request.args),
                    headers=dict(request.headers),
                    remote_addr=request.remote_addr or "unknown",
                    user_agent=request.headers.get('User-Agent', ''),
                    content_length=request.content_length or 0
                )

                # Store request ID for use in after_request
                g.request_id = request_id
                g.request_start_time = time.time()

            @app.after_request
            def after_request(response):
                from flask import g

                if hasattr(g, 'request_id'):
                    # Calculate response size
                    response_size = 0
                    if hasattr(response, 'content_length') and response.content_length:
                        response_size = response.content_length
                    elif hasattr(response, 'data'):
                        response_size = len(response.data)

                    self.log_request_end(
                        request_id=g.request_id,
                        status_code=response.status_code,
                        response_size=response_size
                    )

                return response

            @app.errorhandler(Exception)
            def handle_exception(e):
                from flask import g

                if hasattr(g, 'request_id'):
                    # Log the error
                    error_message = str(e)
                    status_code = getattr(e, 'code', 500)

                    self.log_request_end(
                        request_id=g.request_id,
                        status_code=status_code,
                        error_message=error_message
                    )

                # Re-raise the exception
                raise e

        return flask_logging_middleware

    def create_performance_decorator(self):
        """Create a decorator for API endpoint performance monitoring"""
        def api_performance_decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                operation_name = f"api_{func.__name__}"

                try:
                    with self.perf_logger.measure_operation(operation_name, **kwargs):
                        result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    self.logger.error(f"API endpoint error: {func.__name__}", exc_info=True, extra={
                        "event_type": "api_endpoint_error",
                        "endpoint": func.__name__,
                        "error_message": str(e),
                        "args": str(args),
                        "kwargs": str(kwargs)
                    })
                    raise

            return wrapper
        return api_performance_decorator

    def get_api_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive API performance summary"""
        current_time = time.time()

        summary = {
            "service": self.service_name,
            "timestamp": current_time,
            "request_statistics": {
                "active_requests": len(self.active_requests),
                "total_requests_history": len(self.request_history),
                "recent_requests": len([r for r, _ in self.request_history
                                      if current_time - r.timestamp < 300])  # Last 5 minutes
            },
            "endpoint_performance": {},
            "security_statistics": {
                "total_security_events": len(self.security_events),
                "recent_security_events": len([e for e in self.security_events
                                             if current_time - e.timestamp < 3600]),  # Last hour
                "rate_limit_violations": dict(self.rate_limit_violations)
            }
        }

        # Add endpoint performance data
        for endpoint, metrics in self.endpoint_metrics.items():
            if metrics["total_requests"] > 0:
                avg_time = metrics["total_time"] / metrics["total_requests"]
                success_rate = (metrics["success_count"] / metrics["total_requests"]) * 100

                summary["endpoint_performance"][endpoint] = {
                    "total_requests": metrics["total_requests"],
                    "success_rate_percent": round(success_rate, 2),
                    "average_response_time_seconds": round(avg_time, 4),
                    "min_response_time_seconds": round(metrics["min_time"], 4),
                    "max_response_time_seconds": round(metrics["max_time"], 4),
                    "error_count": metrics["error_count"],
                    "status_codes": dict(metrics["status_codes"])
                }

        return summary

    def get_security_report(self) -> Dict[str, Any]:
        """Generate detailed security report"""
        current_time = time.time()

        # Group security events by type
        events_by_type = defaultdict(list)
        for event in self.security_events:
            events_by_type[event.event_type].append(event)

        # Group events by IP
        events_by_ip = defaultdict(list)
        for event in self.security_events:
            events_by_ip[event.remote_addr].append(event)

        report = {
            "timestamp": current_time,
            "summary": {
                "total_security_events": len(self.security_events),
                "unique_ips": len(events_by_ip),
                "event_types": len(events_by_type)
            },
            "events_by_type": {},
            "high_risk_ips": [],
            "recent_events": []
        }

        # Add events by type
        for event_type, events in events_by_type.items():
            report["events_by_type"][event_type] = {
                "count": len(events),
                "recent_count": len([e for e in events if current_time - e.timestamp < 3600])
            }

        # Identify high-risk IPs
        for ip, events in events_by_ip.items():
            if len(events) >= 5:  # 5 or more security events
                critical_events = len([e for e in events if e.severity == "critical"])
                report["high_risk_ips"].append({
                    "ip": ip,
                    "total_events": len(events),
                    "critical_events": critical_events,
                    "recent_events": len([e for e in events if current_time - e.timestamp < 3600])
                })

        # Add recent events
        recent_events = [e for e in self.security_events if current_time - e.timestamp < 3600]
        report["recent_events"] = [
            {
                "event_type": e.event_type,
                "severity": e.severity,
                "remote_addr": e.remote_addr,
                "endpoint": e.endpoint,
                "description": e.description,
                "timestamp": e.timestamp
            }
            for e in recent_events[-10:]  # Last 10 events
        ]

        return report

def create_api_logging_middleware():
    """
    Factory function to create an API logging middleware

    Usage:
        middleware = create_api_logging_middleware()
        flask_middleware = middleware.create_flask_middleware()
        flask_middleware(app)
    """
    return APILoggingMiddleware("r2d2_api_server")

# Example Flask integration
def integrate_with_flask_app(app, middleware: APILoggingMiddleware):
    """
    Integrate API logging with a Flask application

    Args:
        app: Flask application instance
        middleware: APILoggingMiddleware instance
    """
    flask_middleware = middleware.create_flask_middleware()
    flask_middleware(app)

    # Add health endpoint
    @app.route('/api/health/logging')
    def logging_health():
        return {
            "status": "healthy",
            "performance": middleware.get_api_performance_summary(),
            "security": middleware.get_security_report()
        }

    middleware.logger.info("Flask integration completed", extra={
        "event_type": "flask_integration_complete",
        "app_name": app.name
    })

if __name__ == "__main__":
    print("🔧 R2D2 API Logging Framework")
    print("=" * 50)

    # Test the middleware
    middleware = create_api_logging_middleware()

    print("✅ API logging middleware created")
    print(f"📁 Logs will be written to: /home/rolo/r2ai/logs/")

    # Simulate API requests
    print("\n🔄 Simulating API requests...")

    # Normal request
    req1 = middleware.log_request_start(
        "GET", "/api/status", "/api/status",
        query_params={"detailed": "true"},
        remote_addr="192.168.1.100",
        user_agent="Mozilla/5.0 (compatible)"
    )
    time.sleep(0.1)
    middleware.log_request_end(req1, 200, 1024)

    # Request with error
    req2 = middleware.log_request_start(
        "POST", "/api/servo/move", "/api/servo/move",
        remote_addr="192.168.1.101",
        content_length=256
    )
    time.sleep(0.05)
    middleware.log_request_end(req2, 400, 128, "Invalid servo channel")

    # Suspicious request
    req3 = middleware.log_request_start(
        "GET", "/api/data", "/api/data",
        query_params={"id": "1' OR '1'='1"},
        remote_addr="10.0.0.50",
        user_agent="sqlmap/1.0"
    )
    time.sleep(0.02)
    middleware.log_request_end(req3, 403, 64, "Blocked")

    print("✅ API requests logged successfully")

    # Show performance summary
    print("\n📊 Performance Summary:")
    summary = middleware.get_api_performance_summary()
    for section, data in summary.items():
        if isinstance(data, dict):
            print(f"  {section}:")
            for key, value in data.items():
                print(f"    {key}: {value}")
        else:
            print(f"  {section}: {data}")

    # Show security report
    print("\n🛡️ Security Report:")
    security = middleware.get_security_report()
    for section, data in security.items():
        if isinstance(data, dict) and section != "recent_events":
            print(f"  {section}:")
            for key, value in data.items():
                print(f"    {key}: {value}")
        elif section == "recent_events":
            print(f"  {section}: {len(data)} events")
        else:
            print(f"  {section}: {data}")

    print("\n✅ API logging framework ready!")