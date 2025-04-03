from datetime import date
from decimal import Decimal

from django.utils import timezone

from rest_framework.test import APITestCase
from rest_framework.exceptions import ValidationError

from core.models import CustomUser as User
from progress.models import WeightLog
from progress.serializers import WeightLogSerializer



class WeightLogSerializerTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@mail.com',
            username='testuser',
            password='securepass123'
        )


    def test_valid_data_creates_log(self):
        data = {'weight_kg': 75.5}
        serializer = WeightLogSerializer(data=data, context={'request': self._fake_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        log = serializer.save()
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.weight_kg, 75.5)
        self.assertEqual(log.date_logged.date(), date.today())


    def test_date_logged_is_read_only(self):
        data = {'weight_kg': 80.0, 'date_logged': '2023-01-01'}
        serializer = WeightLogSerializer(data=data, context={'request': self._fake_request()})
        self.assertTrue(serializer.is_valid())
        log = serializer.save()

        self.assertEqual(log.date_logged.date(), date.today())  # Ignored the input


    def test_prevent_duplicate_log_same_day(self):
        # First log should pass
        WeightLog.objects.create(user=self.user, weight_kg=70.0, date_logged=date.today())

        # Second log on same day should fail
        data = {'weight_kg': 72.0}
        serializer = WeightLogSerializer(data=data, context={'request': self._fake_request()})
        with self.assertRaises(ValidationError) as ctx:
            serializer.is_valid(raise_exception=True)

        self.assertIn("You have already logged your weight today.", str(ctx.exception))


    def test_serializer_output_format(self):
        log = WeightLog.objects.create(
                user=self.user,
                weight_kg=78.3,
                date_logged=timezone.now().date()  
            )
        serializer = WeightLogSerializer(instance=log)
        expected_keys = {'id', 'weight_kg', 'date_logged'}

        self.assertEqual(set(serializer.data.keys()), expected_keys)
        self.assertEqual(serializer.data['weight_kg'], Decimal('78.30'))


    def _fake_request(self):
        """Helper to create a mock request with self.user."""
        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory
        from rest_framework.authentication import SessionAuthentication

        factory = APIRequestFactory()
        raw_request = factory.post('/fake-url/')
        raw_request.user = self.user 
        raw_request._force_auth_user = self.user 
        request = Request(raw_request)

        return request
