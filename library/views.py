from datetime import timedelta

from django.db.models import F, Count, Q
from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK

from .models import Author, Book, Member, Loan
from .serializers import AuthorSerializer, BookSerializer, MemberSerializer, LoanSerializer
from rest_framework.decorators import action
from django.utils import timezone
from .tasks import send_loan_notification

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class CustomPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.select_related(
        'author'
    ).all()
    serializer_class = BookSerializer
    pagination_class = CustomPagination

    @action(detail=True, methods=['post'])
    def loan(self, request, pk=None):
        book = self.get_object()
        if book.available_copies < 1:
            return Response({'error': 'No available copies.'}, status=status.HTTP_400_BAD_REQUEST)
        member_id = request.data.get('member_id')
        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            return Response({'error': 'Member does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        loan = Loan.objects.create(book=book, member=member)
        book.available_copies -= 1
        book.save()
        send_loan_notification.delay(loan.id)
        return Response({'status': 'Book loaned successfully.'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        book = self.get_object()
        member_id = request.data.get('member_id')
        try:
            loan = Loan.objects.get(book=book, member__id=member_id, is_returned=False)
        except Loan.DoesNotExist:
            return Response({'error': 'Active loan does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        loan.is_returned = True
        loan.return_date = timezone.now().date()
        loan.save()
        book.available_copies += 1
        book.save()
        return Response({'status': 'Book returned successfully.'}, status=status.HTTP_200_OK)

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

    @action(detail=False, method=["get"])
    def top_active(self, request, *args, **kwargs):
        top_active_members = Member.objects.filter(
            loans__is_returned=False
        ).annotate(
            active_loans_count=Count('loans', filter=Q(loans__is_returned=False))
        ).order_by('-active_loans_count')[:5]

        response_data = []
        for member in top_active_members:
            response_data.append({
                'id': member.id,
                'username': member.user.username,
                'email': member.user.email,
                'active_loans_count': member.active_loans_count,
            })

        return Response(response_data, status=status.HTTP_200_OK)


class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer

    @action(detail=True, methods=["post"])
    def extend_due_date(self, request, *args, **kwargs):
        additional_due_date = request.data.get("additional_days", None)
        if additional_due_date is None:
            return Response(
                {"status": "Additional days required"},
                status=HTTP_400_BAD_REQUEST
            )

        loan = self.get_object()
        loan.due_date += timedelta(days=additional_due_date)
        loan.save()

        loan.refresh_from_db()

        return Response(
            LoanSerializer(loan).data,
            status=HTTP_200_OK
        )


