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



class WorkoutPlanViewSetTests(APITestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = CustomUser.objects.create_user(
            email="user@example.com", username="user", password="userpass"
        )
        self.admin = CustomUser.objects.create_superuser(
            email="admin@example.com", username="admin", password="adminpass"
        )

        self.exercise1 = Exercise.objects.create(name="Push-Up", category="Strength")
        self.exercise2 = Exercise.objects.create(name="Burpees", category="Cardio")

        self.plan1 = WorkoutPlan.objects.create(name="Morning Burn", description="Cardio-focused plan")
        self.plan1.exercises.add(self.exercise1, self.exercise2)

        self.plan2 = WorkoutPlan.objects.create(name="Evening Power", description="Strength-focused")

        self.list_url = reverse("workoutplan-list")


    def test_public_can_list_workout_plans(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)


    def test_filter_by_search_query(self):
        response = self.client.get(self.list_url, {"search": "Power"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Evening Power")


    def test_ordering_by_name(self):
        response = self.client.get(self.list_url, {"ordering": "name"})
        names = [item["name"] for item in response.data["results"]]
        self.assertEqual(names, sorted(names))


    def test_admin_can_create_workout_plan(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.list_url, {
            "name": "New Plan",
            "description": "Test plan",
            "exercises": [self.exercise1.id]
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WorkoutPlan.objects.count(), 3)


    def test_non_admin_cannot_create_workout_plan(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_url, {
            "name": "Blocked Plan",
            "description": "User should not be allowed"
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_exercises_in_plan_action_returns_related_exercises(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("workoutplan-exercises-in-plan", kwargs={"pk": self.plan1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual({ex["name"] for ex in response.data}, {"Push-Up", "Burpees"})


    def test_admin_can_update_workout_plan(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("workoutplan-detail", kwargs={"pk": self.plan2.pk})
        response = self.client.put(url, {
            "name": "Updated Plan",
            "description": "Updated Desc",
            "exercises": [self.exercise2.pk]
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.plan2.refresh_from_db()
        self.assertEqual(self.plan2.name, "Updated Plan")
        self.assertEqual(self.plan2.exercises.count(), 1)


    def test_non_admin_cannot_delete_plan(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("workoutplan-detail", kwargs={"pk": self.plan1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
