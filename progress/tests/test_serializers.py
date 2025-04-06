from datetime import date
from decimal import Decimal
from PIL import Image
import io

from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
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
        self.assertEqual(log.date_logged, date.today())


    def test_date_logged_is_read_only(self):
        data = {'weight_kg': 80.0, 'date_logged': '2023-01-01'}
        serializer = WeightLogSerializer(data=data, context={'request': self._fake_request()})
        self.assertTrue(serializer.is_valid())
        log = serializer.save()

        self.assertEqual(log.date_logged, date.today())  # Ignored the input


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
        expected_keys = {'id', 'weight_kg', 'date_logged', 'user_id'}

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
        self.assertEqual(log.date_logged, date.today())


    def test_date_logged_is_read_only(self):
        data = {
            'chest_cm': 102.0,
            'date_logged': '2020-01-01'
        }

        serializer = BodyMeasurementSerializer(data=data, context={'request': self._fake_request()})
        self.assertTrue(serializer.is_valid())
        log = serializer.save()

        self.assertNotEqual(str(log.date_logged), '2020-01-01')
        self.assertEqual(log.date_logged, date.today())


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
            'biceps_cm', 'thighs_cm', 'calves_cm', 'neck_cm', 'date_logged', 'user_id'
        }

        self.assertEqual(set(serializer.data.keys()), expected_keys - {'user'})  # 'user' is write-only



def generate_test_image():
    image_io = io.BytesIO()
    image = Image.new("RGB", (100, 100), color="blue")
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    return SimpleUploadedFile("test.jpg", image_io.read(), content_type="image/jpeg")



class ProgressLogSerializerTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='progress@mail.com',
            username='progressuser',
            password='secure123'
        )


    def _fake_request(self):
        factory = APIRequestFactory()
        request = factory.post('/fake-url/')
        request.user = self.user
        request._force_auth_user = self.user
        return Request(request)


    def test_valid_data_creates_log(self):
        data = {
            'title': 'Day 10',
            'note': 'Feeling stronger!'
        }

        serializer = ProgressLogSerializer(data=data, context={'request': self._fake_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        log = serializer.save()

        self.assertEqual(log.user, self.user)
        self.assertEqual(log.title, 'Day 10')
        self.assertEqual(log.note, 'Feeling stronger!')
        self.assertEqual(log.date_logged, date.today())


    def test_image_upload_optional(self):
        fake_image = generate_test_image()

        data = {
            'title': 'With Photo',
            'note': 'Visible results!',
            'image': fake_image
        }

        serializer = ProgressLogSerializer(data=data, context={'request': self._fake_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        log = serializer.save()

        self.assertTrue(log.image.name.startswith("progress_photos/"))


    def test_duplicate_same_day_prevented(self):
        ProgressLog.objects.create(user=self.user, note="First log", date_logged=date.today())

        data = {'note': 'Second log'}
        serializer = ProgressLogSerializer(data=data, context={'request': self._fake_request()})

        with self.assertRaises(ValidationError) as ctx:
            serializer.is_valid(raise_exception=True)

        self.assertIn("You already have a progress log for today.", str(ctx.exception))


    def test_date_logged_is_read_only(self):
        data = {
            'title': 'Override date',
            'note': 'Trying to set a date manually',
            'date_logged': '2000-01-01'
        }

        serializer = ProgressLogSerializer(data=data, context={'request': self._fake_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        log = serializer.save()

        self.assertNotEqual(str(log.date_logged), '2000-01-01')
        self.assertEqual(log.date_logged, date.today())


    def test_serializer_output_format(self):
        log = ProgressLog.objects.create(
            user=self.user,
            title='Check-in',
            note='Progress made!',
            date_logged=timezone.now().date()
        )

        serializer = ProgressLogSerializer(instance=log)
        expected_keys = {'id', 'title', 'note', 'image', 'date_logged'}

        self.assertEqual(set(serializer.data.keys()), expected_keys)  # user is HiddenField
        self.assertEqual(serializer.data['title'], 'Check-in')
        self.assertEqual(serializer.data['note'], 'Progress made!')
        self.assertEqual(serializer.data['date_logged'], str(log.date_logged))
