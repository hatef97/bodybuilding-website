from rest_framework.test import APITestCase

from workouts.models import Exercise
from workouts.serializers import ExerciseSerializer


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
