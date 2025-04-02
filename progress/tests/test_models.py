from datetime import date, timedelta

from django.db.utils import IntegrityError
from django.utils import timezone

from rest_framework.test import APITestCase

from core.models import CustomUser as User
from progress.models import WeightLog



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
        self.assertEqual(log.date_logged.date(), date.today())
        self.assertEqual(str(log), f"{self.user} - 74.25kg on {log.date_logged.date()}")


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
