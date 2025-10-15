"""
SCOUT Metrics API Endpoints

Provides access to parsing performance metrics, success rates,
and system health indicators.
"""

from fastapi import APIRouter, Query
from typing import Optional, Dict, Any
import structlog

from app.core.metrics import get_metrics_collector

logger = structlog.get_logger()
router = APIRouter(prefix="/api/metrics", tags=["metrics"])

@router.get("/health")
async def metrics_health() -> Dict[str, Any]:
    """
    Check metrics collection health status
    """
    metrics_collector = get_metrics_collector()
    event_count = len(metrics_collector.events)

    return {
        "status": "healthy",
        "events_collected": event_count,
        "collection_active": True,
        "storage_path": str(metrics_collector.storage_path)
    }

@router.get("/summary")
async def get_metrics_summary(
    hours: Optional[int] = Query(24, description="Time window in hours", ge=1, le=168)
) -> Dict[str, Any]:
    """
    Get comprehensive metrics summary

    Args:
        hours: Time window in hours (default: 24, max: 168/1 week)

    Returns:
        Dictionary containing parsing metrics, performance data, and breakdowns
    """
    try:
        metrics_collector = get_metrics_collector()
        summary = metrics_collector.get_metrics_summary()

        # Add time window context
        summary["time_window_hours"] = hours
        summary["status"] = "success"

        logger.info(
            "Metrics summary requested",
            time_window_hours=hours,
            total_events=len(metrics_collector.events),
            parse_metrics=summary.get("parsing", {})
        )

        return summary

    except Exception as e:
        logger.error(
            "Failed to generate metrics summary",
            error=str(e),
            error_type=type(e).__name__
        )
        return {
            "status": "error",
            "error": f"Failed to generate metrics: {str(e)}",
            "time_window_hours": hours
        }

@router.get("/parsing")
async def get_parse_metrics(
    hours: Optional[int] = Query(24, description="Time window in hours", ge=1, le=168)
) -> Dict[str, Any]:
    """
    Get detailed parsing performance metrics

    Args:
        hours: Time window in hours (default: 24, max: 168/1 week)

    Returns:
        Dictionary containing parse success rates, durations, and breakdowns
    """
    try:
        metrics_collector = get_metrics_collector()
        parse_metrics = metrics_collector.get_parse_metrics(since_hours=hours)

        result = {
            "status": "success",
            "time_window_hours": hours,
            "metrics": {
                "total_parses": parse_metrics.total_parses,
                "successful_parses": parse_metrics.successful_parses,
                "failed_parses": parse_metrics.failed_parses,
                "success_rate_percent": round(parse_metrics.success_rate, 2),
                "failure_rate_percent": round(parse_metrics.failure_rate, 2),
                "average_duration_ms": round(parse_metrics.average_duration_ms, 2),
                "average_sections_per_parse": round(parse_metrics.average_sections_per_parse, 2),
                "average_skills_per_parse": round(parse_metrics.average_skills_per_parse, 2),
                "total_warnings": parse_metrics.total_warnings
            }
        }

        logger.info(
            "Parse metrics requested",
            time_window_hours=hours,
            total_parses=parse_metrics.total_parses,
            success_rate=parse_metrics.success_rate
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to generate parse metrics",
            error=str(e),
            error_type=type(e).__name__
        )
        return {
            "status": "error",
            "error": f"Failed to generate parse metrics: {str(e)}",
            "time_window_hours": hours
        }

@router.get("/events")
async def get_recent_events(
    limit: Optional[int] = Query(100, description="Maximum number of events", ge=1, le=1000)
) -> Dict[str, Any]:
    """
    Get recent metric events for debugging and monitoring

    Args:
        limit: Maximum number of events to return (default: 100, max: 1000)

    Returns:
        List of recent metric events with timestamps and metadata
    """
    try:
        metrics_collector = get_metrics_collector()
        events = metrics_collector.get_recent_events(limit=limit)

        logger.info(
            "Recent events requested",
            limit=limit,
            events_returned=len(events)
        )

        return {
            "status": "success",
            "limit": limit,
            "events_returned": len(events),
            "events": events
        }

    except Exception as e:
        logger.error(
            "Failed to fetch recent events",
            error=str(e),
            error_type=type(e).__name__
        )
        return {
            "status": "error",
            "error": f"Failed to fetch events: {str(e)}",
            "limit": limit,
            "events": []
        }

@router.post("/persist")
async def persist_metrics() -> Dict[str, Any]:
    """
    Save current metrics to disk storage

    Returns:
        Status of persistence operation
    """
    try:
        metrics_collector = get_metrics_collector()
        await metrics_collector.persist_metrics()

        logger.info("Metrics persisted to disk")

        return {
            "status": "success",
            "message": "Metrics successfully persisted",
            "storage_path": str(metrics_collector.storage_path)
        }

    except Exception as e:
        logger.error(
            "Failed to persist metrics",
            error=str(e),
            error_type=type(e).__name__
        )
        return {
            "status": "error",
            "error": f"Failed to persist metrics: {str(e)}"
        }

@router.post("/reset")
async def reset_metrics() -> Dict[str, Any]:
    """
    Clear all collected metrics (use with caution)

    Returns:
        Status of reset operation
    """
    try:
        metrics_collector = get_metrics_collector()
        event_count_before = len(metrics_collector.events)

        metrics_collector.reset_metrics()

        logger.warning(
            "Metrics reset performed",
            events_cleared=event_count_before
        )

        return {
            "status": "success",
            "message": "Metrics successfully reset",
            "events_cleared": event_count_before
        }

    except Exception as e:
        logger.error(
            "Failed to reset metrics",
            error=str(e),
            error_type=type(e).__name__
        )
        return {
            "status": "error",
            "error": f"Failed to reset metrics: {str(e)}"
        }