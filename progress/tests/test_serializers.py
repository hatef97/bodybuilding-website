from datetime import date
from decimal import Decimal

from django.utils import timezone

from rest_framework.test import APITestCase
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework.authentication import SessionAuthentication

from core.models import CustomUser as User
from progress.models import *
from progress.serializers import *



class WeightLogSerializerTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@mail.com',
            username='testuser',
            password='securepass123'
        )


    def _fake_request(self):
        """Helper to create a mock request with self.user."""
        factory = APIRequestFactory()
        raw_request = factory.post('/fake-url/')
        raw_request.user = self.user 
        raw_request._force_auth_user = self.user 
        request = Request(raw_request)

        return request


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



class BodyMeasurementSerializerTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='measure@mail.com',
            username='measureuser',
            password='secure123'
        )


    def _fake_request(self):
        factory = APIRequestFactory()
        request = factory.post('/fake-url/')
        request.user = self.user
        request._force_auth_user = self.user
        return Request(request)


    def test_valid_data_creates_measurement(self):
        data = {
            'chest_cm': 100.5,
            'waist_cm': 85.2,
            'hips_cm': 95.0
        }

        serializer = BodyMeasurementSerializer(data=data, context={'request': self._fake_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        log = serializer.save()
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.chest_cm, Decimal('100.5'))
        self.assertEqual(log.waist_cm, Decimal('85.2'))
        self.assertEqual(log.date_logged.date(), date.today())


    def test_date_logged_is_read_only(self):
        data = {
            'chest_cm': 102.0,
            'date_logged': '2020-01-01'
        }

        serializer = BodyMeasurementSerializer(data=data, context={'request': self._fake_request()})
        self.assertTrue(serializer.is_valid())
        log = serializer.save()

        self.assertNotEqual(str(log.date_logged), '2020-01-01')
        self.assertEqual(log.date_logged.date(), date.today())


    def test_duplicate_same_day_prevented(self):
        BodyMeasurement.objects.create(user=self.user, chest_cm=95.0, date_logged=date.today())

        data = {
            'waist_cm': 80.0
        }
        serializer = BodyMeasurementSerializer(data=data, context={'request': self._fake_request()})

        with self.assertRaises(ValidationError) as ctx:
            serializer.is_valid(raise_exception=True)

        self.assertIn("You have already submitted body measurements for today.", str(ctx.exception))


    def test_partial_measurement_allowed(self):
        data = {'waist_cm': 79.5}
        serializer = BodyMeasurementSerializer(data=data, context={'request': self._fake_request()})
        self.assertTrue(serializer.is_valid())

        log = serializer.save()
        self.assertIsNone(log.chest_cm)
        self.assertEqual(log.waist_cm, Decimal('79.5'))


    def test_serializer_output_keys(self):
        log = BodyMeasurement.objects.create(
            user=self.user,
            chest_cm=100.0,
            waist_cm=90.0,
            date_logged=timezone.now().date()
        )

        serializer = BodyMeasurementSerializer(instance=log)
        expected_keys = {
            'id', 'chest_cm', 'waist_cm', 'hips_cm',
            'biceps_cm', 'thighs_cm', 'calves_cm', 'neck_cm', 'date_logged'
        }

        self.assertEqual(set(serializer.data.keys()), expected_keys - {'user'})  # 'user' is write-only
        