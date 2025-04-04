from datetime import date, timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from core.models import CustomUser as User
from progress.models import WeightLog
from rest_framework.authtoken.models import Token


class WeightLogViewSetTests(APITestCase):
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            email="testuser@mail.com",
            username="testuser",
            password="securepass123"
        )
        
        # Create a test token for authentication
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')
        
        # Create some test WeightLog entries
        self.weight_log_1 = WeightLog.objects.create(
            user=self.user,
            weight_kg=75.0,
            date_logged=date.today() - timedelta(days=1)  # yesterday's log
        )
        
        self.weight_log_2 = WeightLog.objects.create(
            user=self.user,
            weight_kg=76.5,
            date_logged=date.today()  # today's log
        )

    def test_list_weight_logs(self):
        # List weight logs for authenticated user
        url = reverse('weightlog-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['id'], str(self.weight_log_2.id))  # most recent first

    def test_create_weight_log(self):
        # Create a new weight log
        url = reverse('weightlog-list')
        data = {
            'weight_kg': 78.0
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['weight_kg'], '78.00')  # Should return the decimal formatted correctly
        self.assertEqual(response.data['user'], str(self.user.id))  # Should match the logged-in user

    def test_create_weight_log_unauthorized(self):
        # Try to create a weight log without authentication (should fail)
        self.client.credentials()  # Remove token
        url = reverse('weightlog-list')
        data = {
            'weight_kg': 80.0
        }

        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_today_weight_log(self):
        # Get today's log
        url = reverse('weightlog-today')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['weight_kg'], '76.50')  # today's log
        self.assertEqual(response.data['date_logged'], str(date.today()))

    def test_get_today_weight_log_no_log(self):
        # Create a new user with no log for today
        new_user = User.objects.create_user(
            email="newuser@mail.com",
            username="newuser",
            password="securepass123"
        )
        token = Token.objects.create(user=new_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.key}')
        
        url = reverse('weightlog-today')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "No log for today.")

    def test_pagination(self):
        # Test pagination by creating more logs
        for i in range(15):
            WeightLog.objects.create(
                user=self.user,
                weight_kg=75.0 + i,
                date_logged=date.today() - timedelta(days=i)
            )

        # Now request the first page with a page size of 10
        url = reverse('weightlog-list') + '?page=1&page_size=10'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)  # Only 10 items per page
        self.assertEqual(response.data[0]['weight_kg'], '85.00')  # The first item on the page should be the latest one
        
    def test_filter_logs_by_user(self):
        # Ensure that only logs for the authenticated user are returned
        another_user = User.objects.create_user(
            email="anotheruser@mail.com",
            username="anotheruser",
            password="securepass123"
        )
        WeightLog.objects.create(
            user=another_user,
            weight_kg=70.0,
            date_logged=date.today()
        )

        url = reverse('weightlog-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only logs for the logged-in user should be shown
        self.assertEqual(response.data[0]['user'], str(self.user.id))  # Logs should belong to the authenticated user
