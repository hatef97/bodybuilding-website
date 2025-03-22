from datetime import datetime, date 

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



class WorkoutLogSerializerTests(APITestCase):
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="user@example.com", username="user1", password="testpass123"
        )
        self.exercise = Exercise.objects.create(
            name="Push-up", category="Strength"
        )
        self.plan = WorkoutPlan.objects.create(
            name="Morning Routine", description="Full body wake-up"
        )
        self.plan.exercises.add(self.exercise)

        self.valid_data = {
            "user": self.user.pk,
            "workout_plan": self.plan.pk,
            "duration": 45,
            "notes": "Felt strong today!",
            "date": date.today()
        }


    def test_valid_log_creation(self):
        """Test that serializer successfully creates a WorkoutLog."""
        serializer = WorkoutLogSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        log = serializer.save()

        self.assertIsInstance(log, WorkoutLog)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.workout_plan, self.plan)
        self.assertEqual(log.duration, 45)
        self.assertEqual(log.notes, "Felt strong today!")


    def test_duration_must_be_positive(self):
        """Test that duration <= 0 is rejected."""
        data = self.valid_data.copy()
        data["duration"] = 0
        serializer = WorkoutLogSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("duration", serializer.errors)
        self.assertEqual(serializer.errors["duration"][0], "Duration must be greater than zero.")


    def test_read_only_fields_cannot_be_set(self):
        """Test that id and date fields are read-only."""
        data = self.valid_data.copy()
        data["id"] = 999
        data["date"] = "2023-01-01"

        serializer = WorkoutLogSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        log = serializer.save()

        # Check that these values were ignored
        self.assertNotEqual(log.id, 999)
        self.assertNotEqual(str(log.date), "2023-01-01")


    def test_missing_required_fields(self):
        """Test that missing required fields raises errors."""
        serializer = WorkoutLogSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn("user", serializer.errors)
        self.assertIn("workout_plan", serializer.errors)
        self.assertIn("duration", serializer.errors)


    def test_notes_field_is_optional(self):
        """Test that notes can be omitted."""
        data = self.valid_data.copy()
        data.pop("notes")

        serializer = WorkoutLogSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        log = serializer.save()

        self.assertIsNone(log.notes)



class UserWorkoutLogSerializerTests(APITestCase):
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="loguser@example.com", username="loguser", password="testpass123"
        )
        self.exercise = Exercise.objects.create(name="Plank", category="Strength")
        self.plan = WorkoutPlan.objects.create(name="Core Strength")
        self.plan.exercises.add(self.exercise)
        self.expected_date = date.today().strftime("%B %d, %Y")
        self.log = WorkoutLog.objects.create(
            user=self.user,
            workout_plan=self.plan,
            date=self.expected_date,  
            duration=30,
            notes="Core felt solid."
        )


    def test_serializes_correct_fields(self):
        """Serializer returns the correct renamed fields."""
        serializer = UserWorkoutLogSerializer(instance=self.log)
        data = serializer.data

        self.assertIn("workout_plan_name", data)
        self.assertIn("duration", data)
        self.assertIn("date", data)

        self.assertEqual(data["workout_plan_name"], "Core Strength")
        self.assertEqual(data["duration"], 30)


    def test_custom_date_formatting(self):
        """Date is formatted as 'Month DD, YYYY'."""
        serializer = UserWorkoutLogSerializer(instance=self.log)
        self.assertEqual(serializer.data["date"], self.expected_date)


    def test_read_only_fields_are_ignored_on_input(self):
        """Input data should not allow setting read-only fields."""
        input_data = {
            "user": self.user.pk,
            "workout_plan": self.plan.pk,
            "duration": 45,
            "notes": "test",
            "date": self.expected_date,  # read-only
            "id": 9999             # read-only
        }
        serializer = WorkoutLogSerializer(data=input_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        validated = serializer.validated_data
        self.assertNotIn("date", validated)
        self.assertNotIn("id", validated)


    def test_multiple_logs_serialization(self):
        """Serializer should correctly handle multiple log instances."""
        log2 = WorkoutLog.objects.create(
            user=self.user,
            workout_plan=self.plan,
            date=date(2024, 2, 1),
            duration=45
        )
        logs = WorkoutLog.objects.filter(user=self.user)
        serializer = UserWorkoutLogSerializer(logs, many=True)
        self.assertEqual(len(serializer.data), 2)
        self.assertEqual(serializer.data[0]["workout_plan_name"], "Core Strength")
        self.assertIn("date", serializer.data[0])


    def test_serializer_with_minimal_data(self):
        """Should work even if notes are missing."""
        log = WorkoutLog.objects.create(
            user=self.user,
            workout_plan=self.plan,
            date=self.expected_date,
            duration=20
        )
        serializer = UserWorkoutLogSerializer(instance=log)
        self.assertEqual(serializer.data["duration"], 20)
        self.assertEqual(serializer.data["date"], self.expected_date)
