from datetime import timedelta
from io import BytesIO
from PIL import Image

from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.storage import default_storage

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



class LeaderboardSerializerTests(TestCase):

    def setUp(self):
        # Create test users.
        self.user1 = User.objects.create_user(
            email="user1@test.com", username="user1", password="password123"
        )
        self.user2 = User.objects.create_user(
            email="user2@test.com", username="user2", password="password456"
        )
        
        # Create a test challenge.
        self.challenge = Challenge.objects.create(
            name="Test Challenge",
            description="A challenge for testing purposes.",
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=2),
            is_active=True
        )
        
        self.valid_data = {
            "challenge": self.challenge.pk,
            "score": 100
        }
        
        # Set up the request with user1 attached for serializer context.
        self.factory = APIRequestFactory()
        self.request = self.factory.post('/leaderboards/')
        self.request.user = self.user1


    def test_validate_score_negative(self):
        data = self.valid_data.copy()
        data["score"] = -10  # Negative score to trigger validation error.
        serializer = LeaderboardSerializer(data=data, context={"request": self.request}, partial=True)
        self.assertFalse(serializer.is_valid(), serializer.errors)
        self.assertIn("score", serializer.errors)
        self.assertIn("greater than or equal", serializer.errors["score"][0])


    def test_create_leaderboard_assigns_request_user(self):
        # Explicitly pass the user id (primary key) instead of the user instance
        valid_data_with_user = self.valid_data.copy()
        valid_data_with_user['user'] = self.user1.id  # Pass the user ID (primary key)
        
        serializer = LeaderboardSerializer(data=valid_data_with_user, context={"request": self.request}, partial=True)
        
        is_valid = serializer.is_valid()

        self.assertTrue(is_valid, serializer.errors)  # Validate the data
        leaderboard = serializer.save()
        
        # Assert that the user is assigned correctly
        self.assertEqual(leaderboard.user, self.user1)  # Ensure user1 is assigned
        self.assertEqual(leaderboard.challenge, self.challenge)
        self.assertEqual(leaderboard.score, 100)


    def test_create_leaderboard_with_explicit_user(self):
        validated_data = self.valid_data.copy()
        validated_data["challenge"] = self.challenge
        validated_data["user"] = self.user2  # Explicit user
        leaderboard = LeaderboardSerializer().create(validated_data)
        self.assertEqual(leaderboard.user, self.user2)  # Ensure user2 is retained
        self.assertEqual(leaderboard.challenge, self.challenge)
        self.assertEqual(leaderboard.score, 100)


    def test_unique_together_validator(self):
        # Create an initial leaderboard entry.
        Leaderboard.objects.create(challenge=self.challenge, user=self.user1, score=100)
        
        # Prepare data for the second leaderboard entry with the same user and challenge.
        data = self.valid_data.copy()
        data["user"] = self.user1.id  
        
        serializer = LeaderboardSerializer(data=data, context={"request": self.request}, partial=True)
        
        # Check that the serializer is not valid due to the unique-together constraint violation.
        self.assertFalse(serializer.is_valid(), serializer.errors)
        self.assertIn("non_field_errors", serializer.errors)  
        self.assertEqual(
            serializer.errors["non_field_errors"][0],
            "Each user can have only one leaderboard entry per challenge."
        )


    def test_serializer_output_fields(self):
        leaderboard = Leaderboard.objects.create(challenge=self.challenge, user=self.user1, score=150)
        serializer = LeaderboardSerializer(leaderboard, context={"request": self.request})
        data = serializer.data
        expected_fields = ["id", "challenge", "user", "score"]
        for field in expected_fields:
            self.assertIn(field, data)



class UserProfileSerializerTests(TestCase):

    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(
            username='testuser', password='password123', email='testuser@example.com'
        )

        self.profile = UserProfile.objects.create(user=self.user, bio='Old bio', social_links={})

        # The data that will be used for testing
        self.valid_data = {
            'user': self.user.id,
            'bio': 'This is my bio.',
            'social_links': {'facebook': 'facebook.com/testuser', 'twitter': 'twitter.com/testuser'}
        }


    # Test: Test creating a UserProfile from valid data
    def test_create_user_profile(self):
        # Ensure any existing UserProfile is deleted
        UserProfile.objects.filter(user=self.user).delete()
                
        self.client.force_login(self.user)  # Simulate login
        
        data = {
            'bio': 'This is my bio.',
            'social_links': {'facebook': 'facebook.com/testuser', 'twitter': 'twitter.com/testuser'}
        }

        # Create a request object using APIRequestFactory
        factory = APIRequestFactory()
        request = factory.post('/user_profiles/', data, format='json')  # Ensure format='json'
        request.user = self.user  # Attach the logged-in user to the request
        
        # Now pass the request to the context of the serializer
        serializer = UserProfileSerializer(data=data, context={'request': request})
        
        self.assertTrue(serializer.is_valid())  # Validate the data
        
        # Save the validated data and create the profile
        profile = serializer.save()  
        
        # Assert that the profile is created with the correct user
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.bio, 'This is my bio.')
        self.assertEqual(profile.social_links, {'facebook': 'facebook.com/testuser', 'twitter': 'twitter.com/testuser'})


    # Test: Test creating UserProfile when user is not provided in the data
    def test_create_user_profile_without_user(self):
        # Ensure any existing UserProfile is deleted
        UserProfile.objects.filter(user=self.user).delete()

        # Remove the 'user' field from the data
        invalid_data = self.valid_data.copy()
        invalid_data.pop('user')
        
        # Create an APIRequestFactory to simulate the request
        factory = APIRequestFactory()
        request = factory.post('/user_profiles/', invalid_data, format='json')  # Simulate the POST request
        request.user = self.user  # Attach the logged-in user to the request
        
        # Now pass the request to the context of the serializer
        serializer = UserProfileSerializer(data=invalid_data, context={'request': request})
        
        # Check that serializer is valid
        self.assertTrue(serializer.is_valid())
        profile = serializer.save()

        # Assert the user field is correctly assigned from the request context
        self.assertEqual(profile.user, self.user)


    # Test: Test updating a UserProfile (update fields)
    def test_update_user_profile(self):
        serializer = UserProfileSerializer(instance=self.profile, data={'bio': 'Updated bio', 'social_links': {'facebook': 'newlink.com'}}, partial=True)
        
        self.assertTrue(serializer.is_valid())  # Validate serializer
        updated_profile = serializer.save()  # Save the updated profile
        
        # Assert that the bio and social links were updated
        self.assertEqual(updated_profile.bio, 'Updated bio')
        self.assertEqual(updated_profile.social_links, {'facebook': 'newlink.com'})


    # Test: Test partial update of UserProfile
    def test_partial_update_user_profile(self):
        # Only update the bio (partial update)
        serializer = UserProfileSerializer(instance=self.profile, data={'bio': 'Partially updated bio'}, partial=True)
        
        self.assertTrue(serializer.is_valid())  # Validate serializer
        updated_profile = serializer.save()  # Save the updated profile
        
        # Assert that only the bio was updated
        self.assertEqual(updated_profile.bio, 'Partially updated bio')
        self.assertEqual(updated_profile.social_links, {})  # Ensure social_links remain unchanged


    # Test: Test invalid data (e.g., invalid user field)
    def test_invalid_user_field(self):
        # Test with an invalid user ID (string instead of a valid user ID)
        invalid_data = self.valid_data.copy()
        invalid_data['user'] = 'invalid_user_id'  # Invalid user (should be an integer ID)

        serializer = UserProfileSerializer(data=invalid_data)
        
        # Check that the serializer is not valid because of the invalid 'user' field
        self.assertFalse(serializer.is_valid())  # Should fail validation

        # Assert that 'user' field has an error
        self.assertIn('user', serializer.errors)  # Check that the 'user' field is present in errors

        # Check if the error message is related to the invalid user
        self.assertEqual(str(serializer.errors['user'][0]), 'Incorrect type. Expected pk value, received str.')


    # Test: Test invalid data for 'social_links' field (e.g., missing required format)
    def test_invalid_social_links(self):
        invalid_data = self.valid_data.copy()
        invalid_data['social_links'] = 'invalid_social_links'  # Invalid format (should be a dict)
        
        serializer = UserProfileSerializer(data=invalid_data)
        
        # Check that the serializer is invalid
        self.assertFalse(serializer.is_valid())  # Check if it's invalid
        
        # Assert that the social_links field has an error
        self.assertIn('social_links', serializer.errors)  # Check that the 'social_links' field is in errors
        
        # Check if the error message is the one defined in the validation
        self.assertEqual(str(serializer.errors['social_links'][0]), "Social links must be a dictionary.")


    # Test: Test the profile picture (no image provided)
    def test_profile_picture_not_provided(self):
        serializer = UserProfileSerializer(instance=self.profile, data={'bio': 'New bio without picture'}, partial=True)
        
        self.assertTrue(serializer.is_valid())  # Ensure the serializer is valid
        updated_profile = serializer.save()
        
        # Ensure the profile picture field is None or empty (no image provided)
        self.assertEqual(updated_profile.profile_picture.name, None)  # Check if the profile picture is empty or not set


    # Test: Test the profile picture (image provided)
    def test_profile_picture_uploaded(self):
        # Ensure any existing UserProfile is deleted
        UserProfile.objects.filter(user=self.user).delete()
        
        # Create a valid image in memory using Pillow
        image = Image.new('RGB', (100, 100), color='red')
        image_file = BytesIO()
        image.save(image_file, format='JPEG')
        image_file.seek(0)
        
        # Create the InMemoryUploadedFile from the image
        image_uploaded_file = InMemoryUploadedFile(image_file, None, 'profile_pic.jpg', 'image/jpeg', len(image_file.getvalue()), None)
        
        data_with_picture = self.valid_data.copy()
        data_with_picture['profile_picture'] = image_uploaded_file  # Add image to the data
        
        # Create the serializer with the image data
        serializer = UserProfileSerializer(data=data_with_picture)
        
        self.assertTrue(serializer.is_valid(), serializer.errors)  # Validate serializer
        
        # Save the profile and return the updated profile
        profile_with_picture = serializer.save()  
        
        # Assert that the profile picture is correctly set
        self.assertIsNotNone(profile_with_picture.profile_picture)  # Ensure profile picture is not None
        
        # Get the actual file path from the default storage system
        file_path = profile_with_picture.profile_picture.name
        
        # Assert that the file name is correct (it may have a directory path prefix depending on your storage system)
        self.assertTrue(file_path.endswith('profile_pic.jpg'), f"Expected file path to end with 'profile_pic.jpg', got {file_path}")
