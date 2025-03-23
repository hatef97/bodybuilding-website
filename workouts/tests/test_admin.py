from datetime import timedelta

from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.utils import timezone
from django.contrib.messages.storage.fallback import FallbackStorage

from workouts.models import Exercise, WorkoutPlan, WorkoutLog
from workouts.admin import ExerciseAdmin, WorkoutPlanAdmin, WorkoutLogAdmin
from core.models import CustomUser



class MockRequest:
    pass



class ExerciseAdminTests(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.admin = ExerciseAdmin(Exercise, self.site)
        self.factory = RequestFactory()

        # Test data
        self.exercise1 = Exercise.objects.create(name="Jump Rope", category="Cardio")
        self.exercise2 = Exercise.objects.create(name="Bench Press", category="Strength")


    def _get_request_with_messages(self):
        """
        Create a mock request with message storage attached.
        """
        request = self.factory.get("/")
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)
        return request


    def test_list_display_fields(self):
        """
        Admin list_display should include expected fields.
        """
        expected = ('name', 'category', 'description', 'video_url', 'get_category_display')
        self.assertEqual(self.admin.list_display, expected)


    def test_list_filter_and_search_fields(self):
        """
        Admin list_filter and search_fields should be configured correctly.
        """
        self.assertIn('category', self.admin.list_filter)
        self.assertIn('name', self.admin.search_fields)


    def test_list_editable_fields(self):
        """
        Admin list_editable should allow category editing.
        """
        self.assertIn('category', self.admin.list_editable)


    def test_set_strength_category_action(self):
        """
        Action should set category to 'Strength' for selected items.
        """
        request = self._get_request_with_messages()
        queryset = Exercise.objects.filter(pk=self.exercise1.pk)

        self.admin.set_strength_category(request, queryset)
        self.exercise1.refresh_from_db()
        self.assertEqual(self.exercise1.category, 'Strength')


    def test_set_cardio_category_action(self):
        """
        Action should set category to 'Cardio' for selected items.
        """
        request = self._get_request_with_messages()
        queryset = Exercise.objects.filter(pk=self.exercise2.pk)

        self.admin.set_cardio_category(request, queryset)
        self.exercise2.refresh_from_db()
        self.assertEqual(self.exercise2.category, 'Cardio')


    def test_get_category_display_returns_human_readable_label(self):
        """
        get_category_display should return human-readable category label.
        """
        result = self.admin.get_category_display(self.exercise1)
        self.assertEqual(result, self.exercise1.get_category_display())


    def test_admin_pagination_and_ordering(self):
        """
        Admin should paginate and order by name.
        """
        self.assertEqual(self.admin.list_per_page, 20)
        self.assertEqual(self.admin.ordering, ('name',))



class WorkoutPlanAdminTests(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.admin = WorkoutPlanAdmin(WorkoutPlan, self.site)

        self.exercise1 = Exercise.objects.create(
            name="Push Up",
            description="Push-up for upper body strength",
            category="Strength"
        )
        self.exercise2 = Exercise.objects.create(
            name="Running",
            description="Cardio running",
            category="Cardio"
        )

        self.plan = WorkoutPlan.objects.create(
            name="Beginner Plan",
            description="A full body beginner workout plan.",
            created_at=timezone.now() - timedelta(days=1),
            updated_at=timezone.now()
        )
        self.plan.exercises.set([self.exercise1, self.exercise2])


    def test_list_display_fields(self):
        """
        Admin list_display should show correct columns.
        """
        expected_fields = ('name', 'created_at', 'updated_at', 'exercise_count', 'short_description')
        self.assertEqual(self.admin.list_display, expected_fields)


    def test_list_filter_fields(self):
        """
        Admin list_filter should include expected fields.
        """
        self.assertIn('created_at', self.admin.list_filter)
        self.assertIn('updated_at', self.admin.list_filter)


    def test_search_fields(self):
        """
        Admin search_fields should include name and description.
        """
        self.assertIn('name', self.admin.search_fields)
        self.assertIn('description', self.admin.search_fields)


    def test_pagination_and_ordering(self):
        """
        Admin list pagination and ordering should be set correctly.
        """
        self.assertEqual(self.admin.list_per_page, 20)
        self.assertEqual(self.admin.ordering, ('created_at',))


    def test_date_hierarchy(self):
        """
        Date hierarchy should be set to 'created_at'.
        """
        self.assertEqual(self.admin.date_hierarchy, 'created_at')


    def test_filter_horizontal_includes_exercises(self):
        """
        filter_horizontal should include exercises.
        """
        self.assertIn('exercises', self.admin.filter_horizontal)


    def test_exercise_count_returns_correct_number(self):
        """
        Custom method exercise_count should return correct number of exercises.
        """
        count = self.admin.exercise_count(self.plan)
        self.assertEqual(count, 2)


    def test_short_description_returns_truncated_text(self):
        """
        Custom method short_description should return shortened description if available.
        """
        result = self.admin.short_description(self.plan)
        self.assertTrue(result.startswith("A full body beginner workout"))


    def test_short_description_returns_placeholder(self):
        """
        If no description is provided, short_description should say 'No description'.
        """
        plan = WorkoutPlan.objects.create(name="Empty Plan")
        result = self.admin.short_description(plan)
        self.assertEqual(result, 'No description')



class WorkoutLogAdminTests(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.admin = WorkoutLogAdmin(WorkoutLog, self.site)

        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='password123'
        )

        self.exercise = Exercise.objects.create(
            name="Squat",
            category="Strength"
        )

        self.plan = WorkoutPlan.objects.create(
            name="Leg Day",
            description="Focuses on leg strength"
        )
        self.plan.exercises.set([self.exercise])

        self.log = WorkoutLog.objects.create(
            user=self.user,
            workout_plan=self.plan,
            duration=45,
            notes="Challenging workout with squats and lunges.",
            date=timezone.now().date() - timedelta(days=2)
        )


    def test_list_display_fields(self):
        """
        Admin list_display should show correct fields.
        """
        expected_fields = (
            'user_email',
            'workout_plan_name',
            'date',
            'duration_in_minutes',
            'notes_snippet',
            'formatted_date'
        )
        self.assertEqual(self.admin.list_display, expected_fields)


    def test_list_filter_fields(self):
        """
        Admin list_filter should include expected fields.
        """
        self.assertIn('user', self.admin.list_filter)
        self.assertIn('workout_plan', self.admin.list_filter)
        self.assertIn('date', self.admin.list_filter)


    def test_search_fields(self):
        """
        Admin search_fields should include user email and workout plan name.
        """
        self.assertIn('user__email', self.admin.search_fields)
        self.assertIn('workout_plan__name', self.admin.search_fields)


    def test_list_per_page_and_ordering(self):
        """
        Check pagination and default ordering setup.
        """
        self.assertEqual(self.admin.list_per_page, 20)
        self.assertEqual(self.admin.ordering, ('-date',))


    def test_date_hierarchy(self):
        """
        date_hierarchy should be set correctly.
        """
        self.assertEqual(self.admin.date_hierarchy, 'date')


    def test_user_email_display(self):
        """
        user_email should return correct email.
        """
        result = self.admin.user_email(self.log)
        self.assertEqual(result, 'test@example.com')


    def test_workout_plan_name_display(self):
        """
        workout_plan_name should return correct plan name.
        """
        result = self.admin.workout_plan_name(self.log)
        self.assertEqual(result, 'Leg Day')


    def test_duration_in_minutes_display(self):
        """
        duration_in_minutes should return a readable duration string.
        """
        result = self.admin.duration_in_minutes(self.log)
        self.assertEqual(result, '45 minutes')


    def test_notes_snippet_display(self):
        """
        notes_snippet should return a truncated string of notes.
        """
        result = self.admin.notes_snippet(self.log)
        self.assertTrue(result.startswith('Challenging workout'))


    def test_notes_snippet_empty(self):
        """
        notes_snippet should return placeholder when notes are missing.
        """
        log = WorkoutLog.objects.create(
            user=self.user,
            workout_plan=self.plan,
            duration=30,
            notes=None,
            date=timezone.now().date()
        )
        self.assertEqual(self.admin.notes_snippet(log), 'No notes')


    def test_formatted_date_display(self):
        """
        formatted_date should return date in readable format.
        """
        result = self.admin.formatted_date(self.log)
        self.assertRegex(result, r'^[A-Za-z]{3} \d{2}, \d{4}$')  # Like "Sep 18, 2022"


    def test_inline_instances_with_obj(self):
        """
        get_inline_instances should call parent when obj is provided.
        """
        inlines = self.admin.get_inline_instances(MockRequest(), self.log)
        self.assertIsInstance(inlines, list)


    def test_inline_instances_without_obj(self):
        """
        get_inline_instances should return empty list if obj is None.
        """
        self.assertEqual(self.admin.get_inline_instances(MockRequest()), [])
