"""
Celery configuration for background tasks
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bonding_app.settings')

# Create Celery app
app = Celery('bonding_app')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


# Periodic Tasks Schedule
app.conf.beat_schedule = {
    # Check and update streaks every day at midnight
    'update-streaks-daily': {
        'task': 'apps.gamification.tasks.check_and_update_streaks',
        'schedule': crontab(hour=0, minute=0),  # Every day at midnight
    },
    
    # Send daily activity reminders
    'send-daily-reminders': {
        'task': 'apps.notifications.tasks.send_daily_activity_reminders',
        'schedule': crontab(hour=9, minute=0),  # Every day at 9 AM
    },
    
    # Check for broken streaks and send reminders
    'check-streak-warnings': {
        'task': 'apps.gamification.tasks.send_streak_warning_notifications',
        'schedule': crontab(hour=20, minute=0),  # Every day at 8 PM
    },
    
    # Auto-award milestones
    'check-milestones': {
        'task': 'apps.gamification.tasks.check_and_award_milestones',
        'schedule': crontab(hour=1, minute=0),  # Every day at 1 AM
    },
    
    # Clean up old notifications (older than 30 days)
    'cleanup-old-notifications': {
        'task': 'apps.notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Every Sunday at 2 AM
    },
}

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery"""
    print(f'Request: {self.request!r}')