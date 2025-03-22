from datetime import datetime

from django.utils.timezone import now

from rest_framework.test import APITestCase

from workouts.models import *
from workouts.serializers import *


class ExerciseSerializerTests(APITestCase):

    def setUp(self):
        self.valid_data = {
            "name": "Push-up",
            "description": "Upper body strength exercise",
            "category": "Strength",
            "video_url": "https://example.com/pushup"
        }


    def test_serializer_with_valid_data(self):
        """Serializer should be valid with all correct fields."""
        serializer = ExerciseSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        exercise = serializer.save()
        self.assertIsInstance(exercise, Exercise)
        self.assertEqual(exercise.name, self.valid_data["name"])
        self.assertEqual(exercise.category, self.valid_data["category"])


    def test_serializer_missing_required_fields(self):
        """Serializer should fail when required fields are missing."""
        invalid_data = {
            "description": "Some description",
            "video_url": "https://example.com/video"
        }
        serializer = ExerciseSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)
        self.assertIn("category", serializer.errors)


    def test_invalid_category_rejected(self):
        """Serializer should raise error for invalid category."""
        data = self.valid_data.copy()
        data["category"] = "Flexibility"
        serializer = ExerciseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("category", serializer.errors)

        # Check default Django choices error message
        self.assertIn("is not a valid choice", str(serializer.errors["category"][0]))


    def test_optional_fields_can_be_blank(self):
        """Optional fields like description/video_url can be omitted."""
        data = {
            "name": "Jumping Jacks",
            "category": "Cardio"
        }
        serializer = ExerciseSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        exercise = serializer.save()
        self.assertEqual(exercise.description, None)
        self.assertEqual(exercise.video_url, None)


    def test_serialized_output_matches_instance(self):
        """Serializer returns correct serialized data from instance."""
        exercise = Exercise.objects.create(
            name="Plank",
            category="Strength",
            description="Core strength exercise",
            video_url="https://example.com/plank"
        )
        serializer = ExerciseSerializer(instance=exercise)
        data = serializer.data
        self.assertEqual(data["name"], "Plank")
        self.assertEqual(data["category"], "Strength")
        self.assertEqual(data["description"], "Core strength exercise")
        self.assertEqual(data["video_url"], "https://example.com/plank")



class WorkoutPlanSerializerTests(APITestCase):

    def setUp(self):
        self.valid_data = {
            "name": "Full Body Routine",
            "description": "Covers all muscle groups.",
            "exercises": [
                {
                    "name": "Push-up",
                    "description": "Chest and triceps",
                    "category": "Strength",
                    "video_url": "https://example.com/pushup"
                },
                {
                    "name": "Burpees",
                    "description": "Full-body cardio",
                    "category": "Cardio",
                    "video_url": "https://example.com/burpees"
                }
            ]
        }


    def test_create_workout_plan_with_exercises(self):
        """Test creating workout plan with nested exercises."""
        serializer = WorkoutPlanSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        plan = serializer.save()

        self.assertIsInstance(plan, WorkoutPlan)
        self.assertEqual(plan.name, self.valid_data["name"])
        self.assertEqual(plan.exercises.count(), 2)

        names = plan.exercises.values_list("name", flat=True)
        self.assertIn("Push-up", names)
        self.assertIn("Burpees", names)


    def test_output_serialization_structure(self):
        """Test serialized data contains expected nested structure."""
        plan = WorkoutPlan.objects.create(name="Test Plan", description="Test desc")
        exercise = Exercise.objects.create(name="Plank", category="Strength")
        exercise.workout_plans.add(plan)  # ✅ correct way

        serializer = WorkoutPlanSerializer(instance=plan)
        data = serializer.data

        self.assertEqual(data["name"], "Test Plan")
        self.assertIn("exercises", data)
        self.assertIsInstance(data["exercises"], list)
        self.assertEqual(data["exercises"][0]["name"], "Plank")


    def test_missing_name_field_should_fail(self):
        """Missing required name field should raise validation error."""
        data = self.valid_data.copy()
        del data["name"]
        serializer = WorkoutPlanSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)


    def test_invalid_nested_exercise_data(self):
        """Nested exercise with invalid category should fail."""
        data = self.valid_data.copy()
        data["exercises"][0]["category"] = "Yoga"  # Invalid
        serializer = WorkoutPlanSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("category", serializer.errors["exercises"][0])


    def test_read_only_fields_ignored(self):
        """Read-only fields like 'created_at' cannot be set manually."""
        data = self.valid_data.copy()
        data["created_at"] = datetime(2023, 1, 1).isoformat()
        serializer = WorkoutPlanSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        plan = serializer.save()
        self.assertNotEqual(str(plan.created_at.date()), "2023-01-01")  # Should be now
