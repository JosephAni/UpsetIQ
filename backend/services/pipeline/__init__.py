"""
UpsetIQ Data Pipeline Module

Scheduled data collection and processing pipeline using APScheduler.

Jobs:
- Odds snapshot: Every 15 minutes
- Schedule refresh: Daily at 6 AM
- Injury updates: Every 6 hours
- Reddit sentiment: Every 2 hours
- Twitter sentiment: Every 2 hours
- Feature building: After each data job
- Model scoring: After feature build
- Alert processing: After scoring
"""

from services.pipeline.scheduler import (
    get_scheduler,
    start_scheduler,
    stop_scheduler,
    is_scheduler_running,
    run_job_now,
    get_job_status,
)

__all__ = [
    "get_scheduler",
    "start_scheduler",
    "stop_scheduler",
    "is_scheduler_running",
    "run_job_now",
    "get_job_status",
]
