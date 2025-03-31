import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_system.settings')

app = Celery('library_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.beat_schedule = {
    'check-overdue-loans': {
        'task': 'library.tasks.check_overdue_loans',
        'schedule': crontab(hour="3", minute="30"),
        'options': {
            'queue': 'periodic_tasks'
        }
    }
}
app.autodiscover_tasks()
