from datetime import timedelta

from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.utils import timezone
from django.contrib.messages.storage.fallback import FallbackStorage

from workouts.models import Exercise, WorkoutPlan
from workouts.admin import ExerciseAdmin, WorkoutPlanAdmin



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
