from rest_framework import status
from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model
from django.urls import reverse



CustomUser = get_user_model()



class WorkoutRouterURLTests(APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='user@example.com',
            username='testuser',
            password='securepass123'
        )
        self.admin = CustomUser.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='adminpass123'
        )


    def test_exercise_list_requires_authentication(self):
        url = reverse('exercise-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_workoutplan_list_is_public(self):
        url = reverse('workoutplan-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_workoutlog_list_requires_authentication(self):
        url = reverse('workoutlog-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_admin_can_create_exercise(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('exercise-list')
        data = {
            "name": "Deadlift",
            "category": "Strength",
            "description": "Lift bar from floor",
            "video_url": "https://example.com/deadlift"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_non_admin_cannot_create_exercise(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('exercise-list')
        data = {
            "name": "Pushup",
            "category": "Strength"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
