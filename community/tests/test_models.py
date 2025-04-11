from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile

from community.models import ForumPost, Comment, Challenge, Leaderboard, UserProfile



class ForumPostModelTests(TestCase):

    def setUp(self):
        """Create a test user and a forum post."""
        # Create a test user
        self.user = get_user_model().objects.create_user(
            email="testuser@mail.com", username="testuser", password="password"
        )

        # Create a forum post
        self.forum_post = ForumPost.objects.create(
            user=self.user,
            title="Test Post",
            content="This is a test post for forum discussions.",
        )


    def test_forum_post_creation(self):
        """Test if the forum post can be created successfully."""
        post = ForumPost.objects.get(id=self.forum_post.id)
        self.assertEqual(post.title, "Test Post")
        self.assertEqual(post.content, "This is a test post for forum discussions.")
        self.assertEqual(post.user, self.user)
        self.assertTrue(post.is_active)
    

    def test_forum_post_str_method(self):
        """Test the __str__ method of the ForumPost model."""
        post = ForumPost.objects.get(id=self.forum_post.id)
        self.assertEqual(str(post), "Test Post")


    def test_forum_post_soft_delete(self):
        """Test soft delete functionality via is_active field."""
        post = ForumPost.objects.get(id=self.forum_post.id)
        
        # Post is active by default
        self.assertTrue(post.is_active)

        # Deactivate (soft delete) the post
        post.is_active = False
        post.save()

        post = ForumPost.objects.get(id=self.forum_post.id)
        self.assertFalse(post.is_active)


    def test_forum_post_ordering(self):
        """Test that forum posts are ordered by created_at in descending order."""
        post1 = ForumPost.objects.create(
            user=self.user,
            title="Post 1",
            content="First post in the forum.",
            created_at=timezone.now() - timezone.timedelta(days=1),  # yesterday's date
        )
        post2 = ForumPost.objects.create(
            user=self.user,
            title="Post 2",
            content="Second post in the forum.",
            created_at=timezone.now(),  # today's date
        )

        posts = ForumPost.objects.all()

        # Ensure that posts are ordered by created_at in descending order
        self.assertGreater(posts[0].created_at, posts[1].created_at)


    def test_forum_post_invalid_title(self):
        """Test that a forum post cannot be created with a blank title."""
        with self.assertRaises(ValidationError):
            ForumPost.objects.create(
                user=self.user,
                title="",
                content="This post has no title.",
            )


    def test_forum_post_invalid_content(self):
        """Test that a forum post cannot be created with a blank content."""
        with self.assertRaises(ValidationError):
            ForumPost.objects.create(
                user=self.user,
                title="Valid Title",
                content="",
            )



class CommentModelTests(TestCase):

    def setUp(self):
        """Create test users, forum post, and comment."""
        # Create a test user
        self.user = get_user_model().objects.create_user(
            email="testuser@mail.com", username="testuser", password="password"
        )
        
        # Create a second test user for commenting
        self.another_user = get_user_model().objects.create_user(
            email="anotheruser@mail.com", username="anotheruser", password="password"
        )
        
        # Create a forum post
        self.forum_post = ForumPost.objects.create(
            user=self.user,
            title="Test Forum Post",
            content="This is a test post for forum discussions.",
        )

        # Create a comment on the forum post
        self.comment = Comment.objects.create(
            user=self.user,
            post=self.forum_post,
            content="This is a test comment."
        )


    def test_comment_creation(self):
        """Test if the comment can be created successfully."""
        comment = Comment.objects.get(id=self.comment.id)
        self.assertEqual(comment.content, "This is a test comment.")
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.post, self.forum_post)
        self.assertTrue(comment.is_active)


    def test_comment_str_method(self):
        """Test the __str__ method of the Comment model."""
        comment = Comment.objects.get(id=self.comment.id)
        self.assertEqual(str(comment), f"Comment by {self.user.username} on {self.forum_post.title}")


    def test_comment_soft_delete(self):
        """Test soft delete functionality via is_active field."""
        comment = Comment.objects.get(id=self.comment.id)
        
        # Comment is active by default
        self.assertTrue(comment.is_active)

        # Deactivate (soft delete) the comment
        comment.is_active = False
        comment.save()

        comment = Comment.objects.get(id=self.comment.id)
        self.assertFalse(comment.is_active)


    def test_comment_ordering(self):
        """Test that comments are ordered by created_at in ascending order."""
        comment1 = Comment.objects.create(
            user=self.another_user,
            post=self.forum_post,
            content="Another comment",
            created_at=timezone.now() - timezone.timedelta(days=1)  # yesterday's date
        )
        comment2 = Comment.objects.create(
            user=self.user,
            post=self.forum_post,
            content="New comment",
            created_at=timezone.now()  # today's date
        )

        comments = Comment.objects.all()

        # Ensure that comments are ordered by created_at in ascending order
        self.assertGreater(comments[1].created_at, comments[0].created_at)


    def test_invalid_comment_content(self):
        """Test that a comment cannot be created with blank content."""
        comment = Comment(user=self.user, post=self.forum_post, content="")
        
        # This should raise a ValidationError because content is empty
        with self.assertRaises(ValidationError):
            comment.clean()  # Manually trigger the clean method
            comment.save()  # Attempt to save the comment



class ChallengeModelTests(TestCase):

    def setUp(self):
        """Set up a test user and challenge data."""
        # Create a test user
        self.user = get_user_model().objects.create_user(
            email="testuser@mail.com", username="testuser", password="password"
        )

        # Create a challenge
        self.challenge = Challenge.objects.create(
            name="Test Challenge",
            description="This is a test challenge.",
            start_date=timezone.now() + timezone.timedelta(days=1),  # Tomorrow
            end_date=timezone.now() + timezone.timedelta(days=5),  # 5 days from now
        )


    def test_challenge_creation(self):
        """Test that a challenge can be created successfully."""
        challenge = Challenge.objects.get(id=self.challenge.id)
        self.assertEqual(challenge.name, "Test Challenge")
        self.assertEqual(challenge.description, "This is a test challenge.")
        self.assertTrue(challenge.start_date > timezone.now())  # Ensure start date is in the future
        self.assertTrue(challenge.end_date > challenge.start_date)  # Ensure end date is after start date
        self.assertTrue(challenge.is_active)  # By default, the challenge should be active


    def test_challenge_invalid_end_date(self):
        """Test that a challenge cannot be created with an end date earlier than the start date."""
        invalid_end_date = timezone.now() - timezone.timedelta(days=1)  # End date in the past
        challenge = Challenge(
            name="Invalid Challenge",
            description="This challenge has an invalid date.",
            start_date=timezone.now() + timezone.timedelta(days=1),
            end_date=invalid_end_date,
        )
        with self.assertRaises(ValidationError):
            challenge.full_clean()  # This will call the clean() method and raise ValidationError if invalid
            challenge.save()  # Will not reach this point if ValidationError is raised


    def test_challenge_soft_delete(self):
        """Test the soft delete functionality via the is_active field."""
        challenge = Challenge.objects.get(id=self.challenge.id)
        
        # Challenge should be active by default
        self.assertTrue(challenge.is_active)

        # Deactivate (soft delete) the challenge
        challenge.is_active = False
        challenge.save()

        # Fetch the challenge and verify the soft delete
        challenge = Challenge.objects.get(id=self.challenge.id)
        self.assertFalse(challenge.is_active)


    def test_adding_participants(self):
        """Test that users can be added as participants to a challenge."""
        challenge = self.challenge

        # Add the test user as a participant
        challenge.participants.add(self.user)

        # Verify the user is added to the participants
        self.assertIn(self.user, challenge.participants.all())


    def test_challenge_str_method(self):
        """Test the __str__ method of the Challenge model."""
        challenge = Challenge.objects.get(id=self.challenge.id)
        self.assertEqual(str(challenge), "Test Challenge")



class LeaderboardModelTests(TestCase):

    def setUp(self):
        """Set up test users and a challenge for leaderboard tests."""
        # Create a test user
        self.user_1 = get_user_model().objects.create_user(
            email="testuser1@mail.com", username="testuser1", password="password"
        )
        self.user_2 = get_user_model().objects.create_user(
            email="testuser2@mail.com", username="testuser2", password="password"
        )

        # Create a challenge
        self.challenge = Challenge.objects.create(
            name="Test Challenge",
            description="This is a test challenge.",
            start_date=timezone.now() + timezone.timedelta(days=1),  # Tomorrow
            end_date=timezone.now() + timezone.timedelta(days=5),  # 5 days from now
        )

        # Create leaderboard entries
        self.leaderboard_1 = Leaderboard.objects.create(
            challenge=self.challenge,
            user=self.user_1,
            score=100,
        )

        self.leaderboard_2 = Leaderboard.objects.create(
            challenge=self.challenge,
            user=self.user_2,
            score=150,
        )


    def test_leaderboard_creation(self):
        """Test if a leaderboard entry can be created successfully."""
        leaderboard = Leaderboard.objects.get(id=self.leaderboard_1.id)
        self.assertEqual(leaderboard.challenge, self.challenge)
        self.assertEqual(leaderboard.user, self.user_1)
        self.assertEqual(leaderboard.score, 100)


    def test_leaderboard_str_method(self):
        """Test the __str__ method of the Leaderboard model."""
        leaderboard = Leaderboard.objects.get(id=self.leaderboard_1.id)
        self.assertEqual(str(leaderboard), "testuser1 - Test Challenge - 100")


    def test_leaderboard_ordering(self):
        """Test that leaderboard entries are ordered by score in descending order."""
        # Clear out existing leaderboard entries and challenges to avoid duplicates
        Leaderboard.objects.all().delete()
        Challenge.objects.all().delete()
        get_user_model().objects.all().delete()  # Delete all users

        # Create a test user
        self.user_1 = get_user_model().objects.create_user(
            email="testuser1@mail.com", username="testuser1", password="password"
        )
        self.user_2 = get_user_model().objects.create_user(
            email="testuser2@mail.com", username="testuser2", password="password"
        ) 
        self.user_3 = get_user_model().objects.create_user(
            email="user3@mail.com", username="testuser3", password="password"
        )

        # Create a challenge
        self.challenge = Challenge.objects.create(
            name="Test Challenge",
            description="This is a test challenge.",
            start_date=timezone.now() + timezone.timedelta(days=1),  # Tomorrow
            end_date=timezone.now() + timezone.timedelta(days=5),  # 5 days from now
        )

        leaderboard_1 = Leaderboard.objects.create(
            challenge=self.challenge,
            user=self.user_1,
            score=100
        )
        leaderboard_2 = Leaderboard.objects.create(
            challenge=self.challenge,
            user=self.user_2,
            score=200
        )
        leaderboard_3 = Leaderboard.objects.create(
            challenge=self.challenge,
            user=self.user_3,
            score=150
        )

        leaderboards = Leaderboard.objects.all().order_by('-score')

        # Ensure that leaderboard entries are ordered by score in descending order
        self.assertGreater(leaderboards[0].score, leaderboards[1].score)
        self.assertGreater(leaderboards[1].score, leaderboards[2].score)


    def test_leaderboard_unique_constraint(self):
        """Test the unique constraint that each user can have only one leaderboard entry per challenge."""
        # Clear out existing leaderboard entries and challenges to avoid duplicates
        Leaderboard.objects.all().delete()
        Challenge.objects.all().delete()
        get_user_model().objects.all().delete()  # Delete all users        
        
        # Create a test user
        self.user_1 = get_user_model().objects.create_user(
            email="testuser1@mail.com", username="testuser1", password="password"
        )        
        
        # Create a challenge
        self.challenge = Challenge.objects.create(
            name="Test Challenge",
            description="This is a test challenge.",
            start_date=timezone.now() + timezone.timedelta(days=1),  # Tomorrow
            end_date=timezone.now() + timezone.timedelta(days=5),  # 5 days from now
        )        
        
        leaderboard_1 = Leaderboard.objects.create(
            challenge=self.challenge,
            user=self.user_1,
            score=100
        )

        with self.assertRaises(IntegrityError):
            # Trying to insert a duplicate entry for the same challenge and user should raise IntegrityError
            Leaderboard.objects.create(
                challenge=self.challenge,
                user=self.user_1,
                score=200
            )


    def test_leaderboard_score_validation(self):
        """Test that leaderboard entries must have a positive score."""
        # Try to create a leaderboard with a negative score or zero (invalid input)
        leaderboard = Leaderboard(
            challenge=self.challenge,
            user=self.user_1,
            score=-10
        )
        with self.assertRaises(ValidationError):
            leaderboard.full_clean()
            leaderboard.save()

        leaderboard = Leaderboard(
            challenge=self.challenge,
            user=self.user_2,
            score=0
        )
        with self.assertRaises(ValidationError):
            leaderboard.full_clean()
            leaderboard.save()


    def test_leaderboard_unique_per_user_challenge(self):
        """Test that the combination of user and challenge is unique."""
        # Create a valid leaderboard entry first
        with self.assertRaises(IntegrityError):
            Leaderboard.objects.create(
                challenge=self.challenge,
                user=self.user_2,
                score=150,
            )



class UserProfileModelTests(TestCase):

    def setUp(self):
        # Create a test user for all test cases
        self.user = get_user_model().objects.create_user(
            email="user@example.com", username="testuser", password="password123"
        )


    def test_create_user_profile_with_required_fields(self):
        """Test that a UserProfile is created with the required fields and defaults."""
        profile = UserProfile.objects.create(user=self.user, bio="Test bio")
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.bio, "Test bio")
        self.assertEqual(profile.social_links, {})  # default value
        # Check that profile_picture is falsy.
        self.assertFalse(profile.profile_picture)
        # Instead of comparing to an empty string, assert that the name attribute is falsy.
        self.assertFalse(profile.profile_picture.name)
        self.assertIsNotNone(profile.created_at)  # auto_now_add sets this field


    def test_str_method(self):
        """Test that __str__ returns the expected string representation."""
        profile = UserProfile.objects.create(user=self.user, bio="Test bio")
        expected_str = f"Profile of {self.user.username}"
        self.assertEqual(str(profile), expected_str)


    def test_unique_user_profile(self):
        """Test that each user can have only one UserProfile."""
        UserProfile.objects.create(user=self.user, bio="Bio 1")
        with self.assertRaises(IntegrityError):
            # Creating a second UserProfile for the same user should fail
            UserProfile.objects.create(user=self.user, bio="Duplicate bio")


    def test_profile_picture_upload(self):
        """Test that uploading a profile picture saves the file with the correct path."""
        # Simulate an image file upload using SimpleUploadedFile.
        image_data = b"dummy image content"
        uploaded_file = SimpleUploadedFile(
            "test_image.jpg", image_data, content_type="image/jpeg"
        )
        profile = UserProfile.objects.create(user=self.user, profile_picture=uploaded_file)
        self.assertTrue(profile.profile_picture.name.startswith("profile_pics/"))


    def test_social_links_default(self):
        """Test that social_links default to an empty dictionary."""
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(profile.social_links, {})


    def test_social_links_update(self):
        """Test that social_links can be updated and saved correctly."""
        profile = UserProfile.objects.create(user=self.user)
        new_links = {
            "facebook": "http://facebook.com/testuser",
            "twitter": "http://twitter.com/testuser"
        }
        profile.social_links = new_links
        profile.save()
        profile.refresh_from_db()
        self.assertEqual(profile.social_links, new_links)


    def test_bio_can_be_blank(self):
        """Test that bio can be set to an empty string."""
        profile = UserProfile.objects.create(user=self.user, bio="")
        self.assertEqual(profile.bio, "")


    def test_bio_can_be_none(self):
        """Test that bio can be null."""
        profile = UserProfile.objects.create(user=self.user, bio=None)
        self.assertIsNone(profile.bio)
