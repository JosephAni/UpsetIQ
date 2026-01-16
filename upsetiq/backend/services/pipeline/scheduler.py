"""APScheduler setup and job management for UpsetIQ pipeline."""
import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import (
    EVENT_JOB_EXECUTED,
    EVENT_JOB_ERROR,
    EVENT_JOB_MISSED,
    JobExecutionEvent,
)
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None

# Job configuration with intervals
JOB_CONFIG = {
    "odds_snapshot": {
        "func": "services.pipeline.jobs.odds_job:run_odds_snapshot",
        "trigger": IntervalTrigger(minutes=15),
        "description": "Capture odds snapshot from The Odds API",
        "enabled": True,
    },
    "schedule_refresh": {
        "func": "services.pipeline.jobs.schedule_job:run_schedule_refresh",
        "trigger": CronTrigger(hour=6, minute=0),  # Daily at 6 AM
        "description": "Refresh game schedules from SportsDataIO",
        "enabled": True,
    },
    "injury_update": {
        "func": "services.pipeline.jobs.injury_job:run_injury_update",
        "trigger": IntervalTrigger(hours=6),
        "description": "Update injury reports from SportsDataIO",
        "enabled": True,
    },
    "reddit_sentiment": {
        "func": "services.pipeline.jobs.reddit_job:run_reddit_sentiment",
        "trigger": IntervalTrigger(hours=2),
        "description": "Collect Reddit sentiment from NFL subreddits",
        "enabled": os.getenv("REDDIT_CLIENT_ID") is not None,
    },
    "twitter_sentiment": {
        "func": "services.pipeline.jobs.twitter_job:run_twitter_sentiment",
        "trigger": IntervalTrigger(hours=2),
        "description": "Collect Twitter/X sentiment",
        "enabled": os.getenv("TWITTER_BEARER_TOKEN") is not None,
    },
    "feature_build": {
        "func": "services.pipeline.feature_builder:run_feature_build",
        "trigger": IntervalTrigger(minutes=20),  # After data jobs
        "description": "Build ML features from collected data",
        "enabled": True,
    },
    "model_score": {
        "func": "services.pipeline.model_scorer:run_model_scoring",
        "trigger": IntervalTrigger(minutes=25),  # After feature build
        "description": "Score games with UPS model",
        "enabled": True,
    },
    "alert_process": {
        "func": "services.pipeline.alert_engine:run_alert_processing",
        "trigger": IntervalTrigger(minutes=5),
        "description": "Process and deliver pending alerts",
        "enabled": True,
    },
}


def _job_listener(event: JobExecutionEvent):
    """Handle job execution events for logging and monitoring."""
    job_id = event.job_id
    
    if event.exception:
        logger.error(
            f"Job {job_id} failed with exception: {event.exception}",
            exc_info=True,
        )
    else:
        logger.info(f"Job {job_id} completed successfully")


def _missed_job_listener(event: JobExecutionEvent):
    """Handle missed job events."""
    logger.warning(f"Job {event.job_id} missed its scheduled execution time")


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the scheduler instance."""
    global _scheduler
    
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(
            timezone="UTC",
            job_defaults={
                "coalesce": True,  # Combine missed executions
                "max_instances": 1,  # Only one instance per job
                "misfire_grace_time": 60,  # Allow 60 seconds late
            },
        )
        
        # Add event listeners
        _scheduler.add_listener(_job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        _scheduler.add_listener(_missed_job_listener, EVENT_JOB_MISSED)
        
        logger.info("APScheduler instance created")
    
    return _scheduler


def configure_jobs(scheduler: AsyncIOScheduler) -> None:
    """Configure all pipeline jobs on the scheduler."""
    for job_id, config in JOB_CONFIG.items():
        if not config.get("enabled", True):
            logger.info(f"Skipping disabled job: {job_id}")
            continue
        
        try:
            scheduler.add_job(
                config["func"],
                trigger=config["trigger"],
                id=job_id,
                name=config.get("description", job_id),
                replace_existing=True,
            )
            logger.info(f"Configured job: {job_id}")
        except Exception as e:
            logger.error(f"Error configuring job {job_id}: {e}")


def start_scheduler() -> AsyncIOScheduler:
    """
    Start the scheduler with all configured jobs.
    
    Returns:
        The running scheduler instance
    """
    scheduler = get_scheduler()
    
    if scheduler.running:
        logger.warning("Scheduler already running")
        return scheduler
    
    # Configure jobs before starting
    configure_jobs(scheduler)
    
    # Start the scheduler
    scheduler.start()
    logger.info("Pipeline scheduler started")
    
    # Log scheduled jobs
    jobs = scheduler.get_jobs()
    logger.info(f"Scheduled {len(jobs)} jobs:")
    for job in jobs:
        logger.info(f"  - {job.id}: next run at {job.next_run_time}")
    
    return scheduler


def stop_scheduler() -> None:
    """Stop the scheduler gracefully."""
    global _scheduler
    
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=True)
        logger.info("Pipeline scheduler stopped")


def is_scheduler_running() -> bool:
    """Check if scheduler is currently running."""
    return _scheduler is not None and _scheduler.running


def run_job_now(job_id: str) -> bool:
    """
    Manually trigger a job to run immediately.
    
    Args:
        job_id: The job identifier (e.g., "odds_snapshot")
        
    Returns:
        True if job was triggered, False otherwise
    """
    scheduler = get_scheduler()
    
    if not scheduler.running:
        logger.error("Scheduler not running")
        return False
    
    job = scheduler.get_job(job_id)
    if not job:
        logger.error(f"Job not found: {job_id}")
        return False
    
    try:
        job.modify(next_run_time=datetime.now(timezone.utc))
        logger.info(f"Triggered immediate execution of job: {job_id}")
        return True
    except Exception as e:
        logger.error(f"Error triggering job {job_id}: {e}")
        return False


def get_job_status() -> List[Dict[str, Any]]:
    """
    Get status of all scheduled jobs.
    
    Returns:
        List of job status dictionaries
    """
    scheduler = get_scheduler()
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
            "pending": job.pending,
        })
    
    return jobs


def pause_job(job_id: str) -> bool:
    """Pause a scheduled job."""
    scheduler = get_scheduler()
    
    try:
        scheduler.pause_job(job_id)
        logger.info(f"Paused job: {job_id}")
        return True
    except Exception as e:
        logger.error(f"Error pausing job {job_id}: {e}")
        return False


def resume_job(job_id: str) -> bool:
    """Resume a paused job."""
    scheduler = get_scheduler()
    
    try:
        scheduler.resume_job(job_id)
        logger.info(f"Resumed job: {job_id}")
        return True
    except Exception as e:
        logger.error(f"Error resuming job {job_id}: {e}")
        return False


def update_job_interval(job_id: str, **trigger_args) -> bool:
    """
    Update a job's trigger interval.
    
    Args:
        job_id: The job identifier
        **trigger_args: Keyword args for IntervalTrigger (minutes, hours, etc.)
        
    Returns:
        True if successful
    """
    scheduler = get_scheduler()
    
    try:
        new_trigger = IntervalTrigger(**trigger_args)
        scheduler.reschedule_job(job_id, trigger=new_trigger)
        logger.info(f"Updated job interval: {job_id} -> {trigger_args}")
        return True
    except Exception as e:
        logger.error(f"Error updating job interval {job_id}: {e}")
        return False
