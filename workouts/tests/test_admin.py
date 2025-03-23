from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage

from workouts.models import Exercise
from workouts.admin import ExerciseAdmin


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
