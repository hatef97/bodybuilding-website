from django.test import TestCase
from django.core.exceptions import ValidationError

from workouts.models import Exercise, WorkoutPlan



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



class WorkoutPlanModelTests(TestCase):

    def setUp(self):
        self.exercise1 = Exercise.objects.create(
            name="Push-up",
            category="Strength"
        )
        self.exercise2 = Exercise.objects.create(
            name="Burpees",
            category="Cardio"
        )


    def test_str_returns_name(self):
        """__str__ should return the name of the workout plan."""
        plan = WorkoutPlan.objects.create(name="Full Body Routine")
        self.assertEqual(str(plan), "Full Body Routine")


    def test_create_workout_plan_with_all_fields(self):
        """Workout plan can be created with all fields filled."""
        plan = WorkoutPlan.objects.create(
            name="Morning Routine",
            description="A simple morning plan."
        )
        plan.exercises.set([self.exercise1, self.exercise2])

        self.assertEqual(plan.name, "Morning Routine")
        self.assertEqual(plan.description, "A simple morning plan.")
        self.assertEqual(plan.exercises.count(), 2)
        self.assertIn(self.exercise1, plan.exercises.all())
        self.assertIn(plan, self.exercise1.workout_plans.all())  # reverse relation


    def test_description_is_optional(self):
        """Workout plan should be valid without a description."""
        plan = WorkoutPlan.objects.create(name="Quick Plan")
        self.assertIsNone(plan.description)


    def test_add_and_remove_exercises(self):
        """Test adding and removing exercises to a workout plan."""
        plan = WorkoutPlan.objects.create(name="Test Plan")
        plan.exercises.add(self.exercise1)
        self.assertEqual(plan.exercises.count(), 1)

        plan.exercises.remove(self.exercise1)
        self.assertEqual(plan.exercises.count(), 0)


    def test_blank_name_should_fail_validation(self):
        """Workout plan name is required and cannot be blank."""
        plan = WorkoutPlan(name="")
        with self.assertRaises(ValidationError):
            plan.full_clean()
