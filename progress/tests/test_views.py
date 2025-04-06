from datetime import date, timedelta
from decimal import Decimal

from rest_framework.test import APITestCase
from rest_framework import status

from django.urls import reverse
from django.utils import timezone

from core.models import CustomUser as User
from progress.models import *



class WeightLogViewSetTests(APITestCase):
    
    def setUp(self):
        # Clear any existing WeightLogs for the user to ensure a clean test setup
        WeightLog.objects.all().delete()
       
        # Create a test user
        self.user = User.objects.create_user(
            email="testuser@mail.com",
            username="testuser",
            password="securepass123"
        )

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
        self.client.force_authenticate(user=self.user)
        url = reverse('weightlog-list')
        response = self.client.get(url)
        # Check if the response is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensure only the 'results' section contains the two logs for the authenticated user
        self.assertEqual(len(response.data['results']), 2)  # Only 2 logs should be returned
        self.assertEqual(str(response.data['results'][0]['id']), str(self.weight_log_2.id))  # most recent first


    def test_create_weight_log(self):
        # Remove any existing weight log for today before starting the test
        WeightLog.objects.filter(user=self.user, date_logged=date.today()).delete()

        # Create a new weight log
        self.client.force_authenticate(user=self.user)        
        url = reverse('weightlog-list')
        
        # Prepare data without the 'date_logged' field, as it will be automatically set by Django
        data = {
            'weight_kg': 80.0,  # valid weight
        }

        # Send POST request
        response = self.client.post(url, data, format='json')
        
        # Check if the response is 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Ensure the new weight log has been created
        weight_log = WeightLog.objects.get(id=response.data['id'])  # Use the ID from the response
        self.assertEqual(weight_log.weight_kg, 80.0)
        self.assertEqual(weight_log.user, self.user)
        # Ensure the date_logged is set to today (automatically set by Django)
        self.assertEqual(weight_log.date_logged, date.today())  # Should match today's date since we didn't pass a date
    
    
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
        self.client.force_authenticate(user=self.user)        
        url = reverse('weightlog-today')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['weight_kg'], Decimal('76.50'))  # today's log
        self.assertEqual(response.data['date_logged'], str(date.today()))


    def test_get_today_weight_log_no_log(self):
        # Create a new user with no log for today
        new_user = User.objects.create_user(
            email="newuser@mail.com",
            username="newuser",
            password="securepass123"
        )
        self.client.force_authenticate(user=new_user)        
        
        url = reverse('weightlog-today')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "No log for today.")



    def test_filter_logs_by_user(self):
        # Ensure the user is authenticated
        self.client.force_authenticate(user=self.user)

        # Send GET request to list the weight logs
        url = reverse('weightlog-list')
        response = self.client.get(url)

        # Check if the response is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if only logs for the authenticated user are returned
        self.assertEqual(len(response.data['results']), 2)  # Only 2 logs should be returned

        # Verify the logs are for the authenticated user by checking the 'user' field
        for log in response.data['results']:
            self.assertEqual(str(log['user_id']), str(self.user.id))  # Check the user ID in the response



class BodyMeasurementViewSetTests(APITestCase):

    def setUp(self):
        """
        Set up the test environment. Create a user, some body measurement logs,
        and a few other test data for the viewset tests.
        """
        # Create a test user
        self.user = User.objects.create_user(
            email="testuser@mail.com",
            username="testuser",
            password="securepass123"
        )

        # Create some body measurements for the user
        self.measurement_1 = BodyMeasurement.objects.create(
            user=self.user,
            chest_cm=90,
            waist_cm=80,
            hips_cm=95,
            biceps_cm=35,
            thighs_cm=50,
            calves_cm=35,
            neck_cm=40,
            date_logged=date.today() - timedelta(days=1)
        )

        self.measurement_2 = BodyMeasurement.objects.create(
            user=self.user,
            chest_cm=92,
            waist_cm=81,
            hips_cm=96,
            biceps_cm=36,
            thighs_cm=51,
            calves_cm=36,
            neck_cm=41,
            date_logged=date.today()
        )

        # Create body measurements for another user, which shouldn't appear in the tests for the first user
        another_user = User.objects.create_user(
            email="anotheruser@mail.com",
            username="anotheruser",
            password="anotherpassword"
        )

        BodyMeasurement.objects.create(
            user=another_user,
            chest_cm=95,
            waist_cm=85,
            hips_cm=100,
            biceps_cm=37,
            thighs_cm=55,
            calves_cm=37,
            neck_cm=42,
            date_logged=date.today() - timedelta(days=2)
        )


    def test_list_body_measurements(self):
        """Test listing body measurements for the authenticated user."""
        self.client.force_authenticate(user=self.user)
        url = reverse('bodymeasurement-list')  # Replace with your actual URL
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Only 2 logs for the authenticated user

        # Ensure the most recent log is the first one
        self.assertEqual(response.data['results'][0]['id'], self.measurement_2.id)
        self.assertEqual(response.data['results'][1]['id'], self.measurement_1.id)


    def test_create_body_measurement(self):       
        """Test creating a new body measurement entry."""
        # Remove any existing weight log for today before starting the test
        BodyMeasurement.objects.filter(user=self.user, date_logged=date.today()).delete()        
        self.client.force_authenticate(user=self.user)
        url = reverse('bodymeasurement-list')  # Replace with your actual URL

        data = {
            'chest_cm': 94,
            'waist_cm': 84,
            'hips_cm': 98,
            'biceps_cm': 38,
            'thighs_cm': 56,
            'calves_cm': 38,
            'neck_cm': 43
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['chest_cm'], 94)
        self.assertEqual(response.data['waist_cm'], 84)

        # Verify that the newly created entry is associated with the logged-in user
        self.assertEqual(response.data['user_id'], self.user.id)

        # Verify that the new body measurement has been created in the database
        new_measurement = BodyMeasurement.objects.get(id=response.data['id'])  # Use the ID from the response
        self.assertEqual(new_measurement.chest_cm, 94)
        self.assertEqual(new_measurement.user, self.user)


    def test_today_body_measurement(self):
        """Test retrieving today's body measurement using the custom 'today' action."""
        self.client.force_authenticate(user=self.user)
        url = reverse('bodymeasurement-today')  # Replace with your actual URL

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.measurement_2.id)  # Check today's measurement

        # Test case when no body measurement is logged for today
        BodyMeasurement.objects.filter(user=self.user, date_logged=date.today()).delete()
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "No measurements logged for today.")


    def test_unauthenticated_user(self):
        """Test that an unauthenticated user cannot access the API."""
        url = reverse('bodymeasurement-list')  # Replace with your actual URL
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
