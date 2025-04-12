from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIRequestFactory

from community.models import ForumPost
from community.serializers import ForumPostSerializer
from core.models import CustomUser as User



class ForumPostSerializerTests(TestCase):

    def setUp(self):
        # Create a test user for our requests and ForumPosts
        self.user = User.objects.create_user(
            email="test@example.com", username="testuser", password="password123"
        )
        # Build a request using DRF's APIRequestFactory; assign our user to this request.
        self.factory = APIRequestFactory()
        self.request = self.factory.post('/forumposts/')
        self.request.user = self.user

        # Valid data for creating a ForumPost (excluding 'user', which should be auto-assigned)
        self.valid_data = {
            "title": "Test Forum Post",
            "content": "This is a test forum post content."
        }


    def test_validate_title_blank(self):
        """
        Test that a title composed solely of whitespace is rejected.
        """
        invalid_data = self.valid_data.copy()
        # Provide a title with only spaces
        invalid_data["title"] = "    "
        serializer = ForumPostSerializer(data=invalid_data, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        # Check that the custom error message is included.
        self.assertIn("title", serializer.errors)
        self.assertEqual(serializer.errors["title"][0], "Title cannot be blank.")


    def test_create_forum_post_assigns_request_user(self):
        """
        Test that when no user is provided in the input, the create method assigns 
        the request.user to the ForumPost.
        """
        serializer = ForumPostSerializer(data=self.valid_data, context={"request": self.request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        forum_post = serializer.save()
        self.assertEqual(forum_post.user, self.user)


    def test_create_forum_post_with_explicit_user(self):
        """
        Test that when validated_data already contains a user, the create method retains 
        that user rather than overriding it from the request.
        
        Note: Since 'user' is a read-only field on the serializer, this test bypasses 
        serializer input validation by directly calling the create() method with a 
        pre-populated validated_data.
        """
        explicit_user = User.objects.create_user(
            email="explicit@example.com", username="explicituser", password="password456"
        )
        # Manually build validated_data including an explicit user
        validated_data = self.valid_data.copy()
        validated_data["user"] = explicit_user
        forum_post = ForumPostSerializer().create(validated_data)
        self.assertEqual(forum_post.user, explicit_user)


    def test_serializer_output_fields(self):
        """
        Test that the output of the serializer contains all required fields.
        """
        # Create a ForumPost instance directly.
        forum_post = ForumPost.objects.create(
            user=self.user,
            title=self.valid_data["title"],
            content=self.valid_data["content"],
            created_at=timezone.now(),
            updated_at=timezone.now(),
            is_active=True
        )
        serializer = ForumPostSerializer(forum_post, context={"request": self.request})
        data = serializer.data
        expected_fields = ["id", "user", "title", "content", "created_at", "updated_at", "is_active"]
        for field in expected_fields:
            self.assertIn(field, data)
