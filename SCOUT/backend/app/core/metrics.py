"""
SCOUT Metrics Collection Service

Implements minimal metrics collection for parsing performance,
success rates, and validation warnings.
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from pathlib import Path

class MetricType(Enum):
    """Types of metrics collected"""
    PARSE_DURATION = "parse_duration"
    PARSE_SUCCESS = "parse_success"
    PARSE_FAILURE = "parse_failure"
    VALIDATION_WARNING = "validation_warning"
    UPLOAD_SIZE = "upload_size"
    SECTIONS_EXTRACTED = "sections_extracted"
    SKILLS_EXTRACTED = "skills_extracted"

@dataclass
class MetricEvent:
    """Individual metric event"""
    timestamp: datetime
    metric_type: MetricType
    value: float
    labels: Dict[str, str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "metric_type": self.metric_type.value,
            "value": self.value,
            "labels": self.labels,
            "metadata": self.metadata
        }

@dataclass
class ParseMetrics:
    """Aggregate parsing metrics"""
    total_parses: int = 0
    successful_parses: int = 0
    failed_parses: int = 0
    average_duration_ms: float = 0.0
    total_warnings: int = 0
    sections_extracted_total: int = 0
    skills_extracted_total: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_parses == 0:
            return 0.0
        return (self.successful_parses / self.total_parses) * 100

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage"""
        return 100.0 - self.success_rate

    @property
    def average_sections_per_parse(self) -> float:
        """Average sections extracted per successful parse"""
        if self.successful_parses == 0:
            return 0.0
        return self.sections_extracted_total / self.successful_parses

    @property
    def average_skills_per_parse(self) -> float:
        """Average skills extracted per successful parse"""
        if self.successful_parses == 0:
            return 0.0
        return self.skills_extracted_total / self.successful_parses

class MetricsCollector:
    """Collects and aggregates SCOUT metrics"""

    def __init__(self, storage_path: Optional[Path] = None):
        self.events: List[MetricEvent] = []
        self.storage_path = storage_path or Path("data/metrics")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    def record_event(self,
                    metric_type: MetricType,
                    value: float,
                    labels: Optional[Dict[str, str]] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record a metric event"""
        event = MetricEvent(
            timestamp=datetime.utcnow(),
            metric_type=metric_type,
            value=value,
            labels=labels or {},
            metadata=metadata or {}
        )
        self.events.append(event)

    def record_parse_start(self, resume_id: str, file_format: str, file_size_bytes: int) -> str:
        """Record parsing start and return trace ID"""
        trace_id = f"parse_{resume_id}_{int(time.time())}"

        self.record_event(
            MetricType.UPLOAD_SIZE,
            value=file_size_bytes,
            labels={
                "resume_id": resume_id,
                "format": file_format,
                "trace_id": trace_id
            }
        )

        return trace_id

    def record_parse_success(self,
                           trace_id: str,
                           duration_ms: float,
                           sections_count: int,
                           skills_count: int,
                           warnings_count: int) -> None:
        """Record successful parse completion"""
        self.record_event(
            MetricType.PARSE_SUCCESS,
            value=1.0,
            labels={"trace_id": trace_id},
            metadata={
                "duration_ms": duration_ms,
                "sections_count": sections_count,
                "skills_count": skills_count,
                "warnings_count": warnings_count
            }
        )

        self.record_event(
            MetricType.PARSE_DURATION,
            value=duration_ms,
            labels={"trace_id": trace_id}
        )

        self.record_event(
            MetricType.SECTIONS_EXTRACTED,
            value=sections_count,
            labels={"trace_id": trace_id}
        )

        self.record_event(
            MetricType.SKILLS_EXTRACTED,
            value=skills_count,
            labels={"trace_id": trace_id}
        )

        if warnings_count > 0:
            self.record_event(
                MetricType.VALIDATION_WARNING,
                value=warnings_count,
                labels={"trace_id": trace_id}
            )

    def record_parse_failure(self, trace_id: str, duration_ms: float, error_type: str) -> None:
        """Record parsing failure"""
        self.record_event(
            MetricType.PARSE_FAILURE,
            value=1.0,
            labels={
                "trace_id": trace_id,
                "error_type": error_type
            },
            metadata={"duration_ms": duration_ms}
        )

        self.record_event(
            MetricType.PARSE_DURATION,
            value=duration_ms,
            labels={"trace_id": trace_id}
        )

    def get_parse_metrics(self, since_hours: int = 24) -> ParseMetrics:
        """Get aggregated parsing metrics for the specified time window"""
        cutoff_time = datetime.utcnow() - timedelta(hours=since_hours)
        recent_events = [e for e in self.events if e.timestamp >= cutoff_time]

        metrics = ParseMetrics()
        durations = []

        for event in recent_events:
            if event.metric_type == MetricType.PARSE_SUCCESS:
                metrics.successful_parses += 1
                metrics.total_parses += 1

                # Extract metadata
                if 'sections_count' in event.metadata:
                    metrics.sections_extracted_total += int(event.metadata['sections_count'])
                if 'skills_count' in event.metadata:
                    metrics.skills_extracted_total += int(event.metadata['skills_count'])
                if 'warnings_count' in event.metadata:
                    metrics.total_warnings += int(event.metadata['warnings_count'])

            elif event.metric_type == MetricType.PARSE_FAILURE:
                metrics.failed_parses += 1
                metrics.total_parses += 1

            elif event.metric_type == MetricType.PARSE_DURATION:
                durations.append(event.value)

        # Calculate average duration
        if durations:
            metrics.average_duration_ms = sum(durations) / len(durations)

        return metrics

    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent events as dictionaries"""
        recent_events = sorted(self.events, key=lambda e: e.timestamp, reverse=True)[:limit]
        return [event.to_dict() for event in recent_events]

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        parse_metrics = self.get_parse_metrics()

        # File format breakdown
        format_counts = {}
        for event in self.events:
            if event.metric_type == MetricType.UPLOAD_SIZE and 'format' in event.labels:
                format_type = event.labels['format']
                format_counts[format_type] = format_counts.get(format_type, 0) + 1

        # Duration percentiles
        durations = [e.value for e in self.events if e.metric_type == MetricType.PARSE_DURATION]
        duration_percentiles = {}
        if durations:
            sorted_durations = sorted(durations)
            duration_percentiles = {
                "p50": sorted_durations[len(sorted_durations) // 2],
                "p90": sorted_durations[int(len(sorted_durations) * 0.9)],
                "p95": sorted_durations[int(len(sorted_durations) * 0.95)],
                "min": min(durations),
                "max": max(durations)
            }

        return {
            "parsing": asdict(parse_metrics),
            "file_formats": format_counts,
            "performance": {
                "duration_percentiles_ms": duration_percentiles,
                "total_events": len(self.events)
            },
            "collection_period": {
                "start": min(e.timestamp for e in self.events).isoformat() if self.events else None,
                "end": max(e.timestamp for e in self.events).isoformat() if self.events else None
            }
        }

    async def persist_metrics(self) -> None:
        """Save metrics to disk"""
        async with self._lock:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_{timestamp}.json"
            filepath = self.storage_path / filename

            data = {
                "collection_timestamp": datetime.utcnow().isoformat(),
                "summary": self.get_metrics_summary(),
                "events": self.get_recent_events()
            }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

    def reset_metrics(self) -> None:
        """Clear all collected metrics"""
        self.events.clear()

# Global metrics collector instance
_metrics_collector = None

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector