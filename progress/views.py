from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework import status

from .models import WeightLog
from .serializers import WeightLogSerializer



class WeightLogPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size'
    max_page_size = 100



class WeightLogViewSet(viewsets.ModelViewSet):
    queryset = WeightLog.objects.all()
    serializer_class = WeightLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = WeightLogPagination

    def get_queryset(self):
        """
        Optionally restricts the returned logs to a given user,
        by filtering against a `user` query parameter in the URL.
        """
        user = self.request.user
        return WeightLog.objects.filter(user=user).order_by('-date_logged')

    def perform_create(self, serializer):
        """
        Override to automatically associate the logged-in user.
        """
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def today(self, request):
        """
        Custom action to get today's weight log (if any).
        """
        user = request.user
        today_log = WeightLog.objects.filter(user=user, date_logged=timezone.now().date()).first()
        if today_log:
            serializer = self.get_serializer(today_log)
            return Response(serializer.data)
        return Response({"detail": "No log for today."}, status=status.HTTP_404_NOT_FOUND)
