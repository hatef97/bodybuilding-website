from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from community.models import ForumPost, Comment



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
            