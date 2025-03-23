from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from django.urls import reverse

from workouts.models import *
from core.models import CustomUser



class ExerciseViewSetTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            email='user@example.com', username='user', password='userpass'
        )
        self.admin = CustomUser.objects.create_superuser(
            email='admin@example.com', username='admin', password='adminpass'
        )

        self.exercise1 = Exercise.objects.create(name="Push-up", category="Strength")
        self.exercise2 = Exercise.objects.create(name="Jumping Jacks", category="Cardio")

        self.list_url = reverse('exercise-list')


    def test_authenticated_user_can_list_exercises(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)


    def test_filter_by_category(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url, {'category': 'Strength'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], "Push-up")


    def test_search_query(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url, {'search': 'jump'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], "Jumping Jacks")


    def test_ordering_by_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url, {'ordering': 'name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [e['name'] for e in response.data['results']]
        self.assertEqual(names, sorted(names))


    def test_non_admin_cannot_create_exercise(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_url, {
            "name": "Squat", "category": "Strength"
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_admin_can_create_exercise(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.list_url, {
            "name": "Squat", "category": "Strength"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Exercise.objects.count(), 3)


    def test_admin_can_update_exercise(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('exercise-detail', kwargs={'pk': self.exercise1.pk})
        response = self.client.put(url, {
            "name": "Push-up Pro", "category": "Strength"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.exercise1.refresh_from_db()
        self.assertEqual(self.exercise1.name, "Push-up Pro")


    def test_non_admin_cannot_delete_exercise(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('exercise-detail', kwargs={'pk': self.exercise2.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
