from django.test import TestCase
from django.core.exceptions import ValidationError

from workouts.models import Exercise



class ExerciseModelTests(TestCase):

    def setUp(self):
        self.exercise = Exercise.objects.create(
            name="Push-up",
            description="Upper body strength exercise",
            category="Strength",
            video_url="https://example.com/pushup"
        )


    def test_str_returns_name(self):
        """__str__ method should return the exercise name."""
        self.assertEqual(str(self.exercise), "Push-up")


    def test_create_exercise_with_all_fields(self):
        """Create an exercise with all fields filled."""
        self.assertEqual(self.exercise.name, "Push-up")
        self.assertEqual(self.exercise.description, "Upper body strength exercise")
        self.assertEqual(self.exercise.category, "Strength")
        self.assertEqual(self.exercise.video_url, "https://example.com/pushup")


    def test_create_exercise_with_optional_fields_blank(self):
        """Exercise should be valid even if optional fields are blank."""
        exercise = Exercise.objects.create(
            name="Jumping Jacks",
            category="Cardio"
        )
        self.assertIsNone(exercise.description)
        self.assertIsNone(exercise.video_url)


    def test_invalid_category_raises_validation_error(self):
        """Invalid category should raise a validation error."""
        exercise = Exercise(
            name="Invalid Exercise",
            category="Flexibility"  # Not allowed
        )
        with self.assertRaises(ValidationError):
            exercise.full_clean()


    def test_blank_name_should_fail_validation(self):
        """Blank name should trigger validation error."""
        exercise = Exercise(name="", category="Strength")
        with self.assertRaises(ValidationError):
            exercise.full_clean()
