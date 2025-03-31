
from celery import shared_task
from django.utils.datetime_safe import datetime

from .models import Loan
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_loan_notification(loan_id):
    try:
        loan = Loan.objects.get(id=loan_id)
        member_email = loan.member.user.email
        book_title = loan.book.title
        send_mail(
            subject='Book Loaned Successfully',
            message=f'Hello {loan.member.user.username},\n\nYou have successfully loaned "{book_title}".\nPlease return it by the due date.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member_email],
            fail_silently=False,
        )
    except Loan.DoesNotExist:
        pass


@shared_task(bind=True, queue='periodic_tasks')
def check_overdue_loans():
    loans = Loan.objects.select_related("member").filter(
        is_returned=False,
        due_date__gte=datetime.now()
    )

    for loan in loans:
        send_mail(
            subject='Book overdue',
            message=f'Hello {loan.member.user.first_name},\n\nYour loan is over booked by the due date {loan.due_date}".',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[loan.member.user.email],
            fail_silently=False,
        )
