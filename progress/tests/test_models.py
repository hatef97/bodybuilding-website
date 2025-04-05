from datetime import date, timedelta

from django.db.utils import IntegrityError
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.test import APITestCase

from core.models import CustomUser as User
from progress.models import WeightLog, BodyMeasurement, ProgressLog



class WeightLogModelTests(APITestCase):

    def setUp(self):
        # Create a CustomUser instance
        self.user = User.objects.create_user(
            email='user@mail.com',
            username='admin1',
            password='userpassword'
        )
        

    def test_create_weight_log(self):
        log = WeightLog.objects.create(user=self.user, weight_kg=74.25)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.weight_kg, 74.25)
        self.assertEqual(log.date_logged, date.today())
        self.assertEqual(str(log), f"{self.user} - 74.25kg on {log.date_logged}")


    def test_weight_log_unique_per_day(self):
        WeightLog.objects.create(user=self.user, weight_kg=80.0)

        with self.assertRaises(IntegrityError):
            WeightLog.objects.create(user=self.user, weight_kg=81.0)


    def test_weight_log_different_users_same_day(self):
        WeightLog.objects.create(user=self.user, weight_kg=75.0)
        another_user = User.objects.create_user(
            email='anotheruser@mail.com', 
            username='anotheruser',
            password='pass456'
         )
        log = WeightLog.objects.create(user=another_user, weight_kg=70.0)

        self.assertEqual(log.weight_kg, 70.0)
        self.assertEqual(log.user.username, 'anotheruser')


    def test_help_text_on_weight_field(self):
        field = WeightLog._meta.get_field('weight_kg')
        self.assertEqual(field.help_text, "Weight in kilograms")


    def test_ordering_desc_by_date_logged(self):
        test_user = User.objects.create_user(
            email='test@mail.com',
            username='ordering_user',
            password='userpassword'
        )

        day1 = date(2024, 1, 1)
        day2 = date(2024, 1, 2)

        WeightLog.objects.create(user=test_user, weight_kg=77.5, date_logged=day2)
        WeightLog.objects.create(user=test_user, weight_kg=76.0, date_logged=day1)

        logs = WeightLog.objects.filter(user=test_user)
        self.assertEqual(list(logs)[0].date_logged, day2)
        self.assertEqual(list(logs)[1].date_logged, day1)



class BodyMeasurementModelTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@mail.com',
            username='testuser',
            password='securepass123'
        )


    def test_create_full_body_measurement(self):
        measurement = BodyMeasurement.objects.create(
            user=self.user,
            chest_cm=100.5,
            waist_cm=85.2,
            hips_cm=95.0,
            biceps_cm=35.5,
            thighs_cm=60.0,
            calves_cm=40.0,
            neck_cm=38.0
        )

        self.assertEqual(measurement.user, self.user)
        self.assertEqual(measurement.chest_cm, 100.5)
        self.assertEqual(measurement.waist_cm, 85.2)
        self.assertEqual(measurement.date_logged.date(), date.today())
        self.assertIn("measurements on", str(measurement))


    def test_create_partial_body_measurement(self):
        measurement = BodyMeasurement.objects.create(
            user=self.user,
            waist_cm=80.0
        )

        self.assertIsNone(measurement.chest_cm)
        self.assertEqual(measurement.waist_cm, 80.0)

    def test_unique_body_measurement_per_day(self):
        BodyMeasurement.objects.create(user=self.user, chest_cm=90.0)

        with self.assertRaises(Exception):  # could be IntegrityError depending on DB
            BodyMeasurement.objects.create(user=self.user, waist_cm=85.0)


    def test_multiple_users_same_day_allowed(self):
        user2 = User.objects.create_user(
            email='user2@mail.com',
            username='user2',
            password='securepass456'
        )

        BodyMeasurement.objects.create(user=self.user, chest_cm=90.0)
        other_measurement = BodyMeasurement.objects.create(user=user2, chest_cm=91.0)

        self.assertEqual(other_measurement.user, user2)
        self.assertEqual(other_measurement.chest_cm, 91.0)


    def test_str_representation(self):
        measurement = BodyMeasurement.objects.create(
            user=self.user,
            chest_cm=99.9,
            date_logged=date(2023, 8, 10)
        )

        self.assertEqual(str(measurement), f"{self.user} measurements on 2023-08-10")


    def test_ordering_by_date_logged_desc(self):
        date1 = timezone.now().date() - timedelta(days=2)
        date2 = timezone.now().date() - timedelta(days=1)

        BodyMeasurement.objects.create(user=self.user, waist_cm=85.0, date_logged=date1)
        BodyMeasurement.objects.create(user=self.user, waist_cm=83.0, date_logged=date2)

        logs = BodyMeasurement.objects.filter(user=self.user)
        self.assertEqual(logs[0].date_logged, date2)
        self.assertEqual(logs[1].date_logged, date1)



class ProgressLogModelTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='loguser@mail.com',
            username='loguser',
            password='securepass123'
        )


    def test_create_progress_log_minimal(self):
        log = ProgressLog.objects.create(
            user=self.user,
            note="Hit a new personal best today!"
        )
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.note, "Hit a new personal best today!")
        self.assertEqual(log.title, "")
        self.assertIsNone(log.image.name)
        self.assertEqual(log.date_logged.date(), date.today())
        self.assertIn("progress log on", str(log))


    def test_create_progress_log_full(self):
        image = SimpleUploadedFile("progress.jpg", b"filecontent", content_type="image/jpeg")
        log = ProgressLog.objects.create(
            user=self.user,
            title="Week 4 Check-In",
            note="Down 2kg, looking leaner!",
            image=image
        )
        self.assertEqual(log.title, "Week 4 Check-In")
        self.assertTrue(log.image.name.startswith("progress_photos/"))


    def test_multiple_logs_same_day_allowed(self):
        ProgressLog.objects.create(user=self.user, note="Morning check-in")
        ProgressLog.objects.create(user=self.user, note="Evening update")

        logs = ProgressLog.objects.filter(user=self.user)
        self.assertEqual(logs.count(), 2)


    def test_str_representation(self):
        log = ProgressLog.objects.create(
            user=self.user,
            title="Milestone",
            note="Hit goal weight!",
            date_logged=date(2024, 1, 1)
        )
        self.assertEqual(str(log), f"{self.user} progress log on 2024-01-01")


    def test_ordering_by_date_logged_desc(self):
        day1 = timezone.now().date() - timedelta(days=2)
        day2 = timezone.now().date() - timedelta(days=1)

        ProgressLog.objects.create(user=self.user, note="Day 1", date_logged=day1)
        ProgressLog.objects.create(user=self.user, note="Day 2", date_logged=day2)

        logs = ProgressLog.objects.filter(user=self.user)
        self.assertEqual(logs[0].date_logged, day2)
        self.assertEqual(logs[1].date_logged, day1)
