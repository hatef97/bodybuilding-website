from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIRequestFactory

from community.models import *
from community.serializers import *
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



class CommentSerializerTests(TestCase):

    def setUp(self):
        # Create a test user and forum post for the tests.
        self.user = User.objects.create_user(
            email="user@test.com", username="testuser", password="password"
        )
        self.forum_post = ForumPost.objects.create(
            user=self.user,
            title="Test Post",
            content="Content of the test post.",
            created_at=timezone.now(),
            updated_at=timezone.now(),
            is_active=True
        )
        # Build a request using DRF's APIRequestFactory and attach our test user.
        self.factory = APIRequestFactory()
        self.request = self.factory.post('/comments/')
        self.request.user = self.user
        
        # Valid data (excluding 'user' which should be automatically assigned).
        self.valid_data = {
            "post": self.forum_post.id,  # Assuming the field expects a primary key.
            "content": "This is a test comment."
        }


    def test_validate_content_blank(self):
        """
        Test that a comment with content consisting solely of whitespace is rejected.
        Expected error: "Comment content cannot be empty."
        """
        invalid_data = self.valid_data.copy()
        invalid_data["content"] = "    "  # Only whitespace
        serializer = CommentSerializer(data=invalid_data, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("content", serializer.errors)
        self.assertEqual(serializer.errors["content"][0], "Comment content cannot be empty.")


    def test_create_comment_assigns_request_user(self):
        """
        Test that when no user is provided in the input, the serializer automatically assigns
        the request.user to the Comment instance.
        """
        serializer = CommentSerializer(data=self.valid_data, context={"request": self.request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        comment = serializer.save()
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.post, self.forum_post)
        self.assertEqual(comment.content, self.valid_data["content"])


    def test_create_comment_with_explicit_user(self):
        """
        Test that if the validated_data already includes a user, the create() method retains that user.
        (Note: The user field is read-only in serializer input but may be set programmatically.)
        """
        explicit_user = User.objects.create_user(
            email="explicit@test.com", username="explicituser", password="password456"
        )
        # Build validated_data with "post" as a ForumPost instance.
        validated_data = {
            "post": self.forum_post,
            "content": "This is a test comment.",
            "user": explicit_user
        }
        comment = CommentSerializer().create(validated_data)
        self.assertEqual(comment.user, explicit_user)
        self.assertEqual(comment.post, self.forum_post)
        self.assertEqual(comment.content, "This is a test comment.")


    def test_serializer_output_fields(self):
        """
        Test that the serializer output contains all the expected fields.
        """
        # Directly create a Comment instance.
        comment = Comment.objects.create(
            user=self.user,
            post=self.forum_post,
            content=self.valid_data["content"],
            created_at=timezone.now(),
            is_active=True
        )
        serializer = CommentSerializer(comment, context={"request": self.request})
        data = serializer.data
        expected_fields = ["id", "user", "post", "content", "created_at", "is_active"]
        for field in expected_fields:
            self.assertIn(field, data)



class ChallengeSerializerTests(TestCase):
    
    def setUp(self):
        # Create test users.
        self.user1 = User.objects.create_user(
            email="user1@test.com", username="user1", password="password123"
        )
        self.user2 = User.objects.create_user(
            email="user2@test.com", username="user2", password="password456"
        )
        
        # Prepare valid challenge data.
        self.start_date = timezone.now() + timedelta(days=1)
        self.end_date = self.start_date + timedelta(days=2)
        self.valid_data = {
            "name": "Test Challenge",
            "description": "This is a test challenge description.",
            "start_date": self.start_date,
            "end_date": self.end_date,
            "is_active": True,
            # 'participants' is optional.
        }
    

    def test_validate_end_date_after_start_date(self):
        """
        Test that the serializer validation fails if end_date is earlier than start_date.
        """
        invalid_data = self.valid_data.copy()
        # Set end_date to before start_date.
        invalid_data["end_date"] = self.start_date - timedelta(hours=1)
        serializer = ChallengeSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        # The error is raised as a non-field error.
        self.assertIn("non_field_errors", serializer.errors)
        self.assertEqual(
            serializer.errors["non_field_errors"][0],
            "End date cannot be earlier than start date."
        )
    

    def test_create_challenge_without_participants(self):
        """
        Test that a challenge can be created without providing participants.
        """
        serializer = ChallengeSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        challenge = serializer.save()
        # Verify regular fields.
        self.assertEqual(challenge.name, self.valid_data["name"])
        self.assertEqual(challenge.description, self.valid_data["description"])
        self.assertEqual(challenge.start_date, self.valid_data["start_date"])
        self.assertEqual(challenge.end_date, self.valid_data["end_date"])
        self.assertTrue(challenge.is_active)
        # No participants should be associated.
        self.assertEqual(challenge.participants.count(), 0)
    

    def test_create_challenge_with_participants(self):
        """
        Test that a challenge can be created when a list of participant user IDs is provided.
        """
        valid_data_with_participants = self.valid_data.copy()
        # Provide participants as a list of primary keys.
        valid_data_with_participants["participants"] = [self.user1.pk, self.user2.pk]
        serializer = ChallengeSerializer(data=valid_data_with_participants)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        challenge = serializer.save()
        # Check that both users have been added to the many-to-many field.
        participants = challenge.participants.all()
        self.assertEqual(participants.count(), 2)
        self.assertIn(self.user1, participants)
        self.assertIn(self.user2, participants)
    

    def test_update_challenge_fields(self):
        """
        Test that updating a challenge instance updates its fields correctly.
        """
        # First, create a challenge without participants.
        serializer = ChallengeSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        challenge = serializer.save()
        
        # Prepare data for updating the challenge.
        new_start_date = self.start_date + timedelta(days=3)
        new_end_date = new_start_date + timedelta(days=2)
        update_data = {
            "name": "Updated Challenge Name",
            "description": "Updated description.",
            "start_date": new_start_date,
            "end_date": new_end_date,
            "is_active": False,
            # Update participants as well.
            "participants": [self.user2.pk],
        }
        updated_challenge = ChallengeSerializer().update(challenge, update_data)
        self.assertEqual(updated_challenge.name, update_data["name"])
        self.assertEqual(updated_challenge.description, update_data["description"])
        self.assertEqual(updated_challenge.start_date, new_start_date)
        self.assertEqual(updated_challenge.end_date, new_end_date)
        self.assertFalse(updated_challenge.is_active)
        # Check that participants have been updated.
        participants = updated_challenge.participants.all()
        self.assertEqual(participants.count(), 1)
        self.assertIn(self.user2, participants)
    

    def test_serializer_output_fields(self):
        """
        Test that the serialized output of a challenge includes all expected fields.
        """
        # Create a challenge with participants.
        challenge = Challenge.objects.create(
            name=self.valid_data["name"],
            description=self.valid_data["description"],
            start_date=self.valid_data["start_date"],
            end_date=self.valid_data["end_date"],
            is_active=self.valid_data["is_active"]
        )
        challenge.participants.set([self.user1.pk, self.user2.pk])
        
        serializer = ChallengeSerializer(challenge)
        data = serializer.data
        
        expected_fields = [
            "id", "name", "description", "start_date", "end_date", 
            "participants", "created_at", "is_active"
        ]
        for field in expected_fields:
            self.assertIn(field, data)
        # Check that participants are returned as a list of IDs.
        self.assertEqual(set(data["participants"]), set([self.user1.pk, self.user2.pk]))
