from datetime import timedelta

from rest_framework.test import APIClient
from rest_framework import status

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from community.models import ForumPost, Comment, Challenge
from core.models import CustomUser as User



class ForumPostViewSetTests(TestCase):

    def setUp(self):
        # Clean up existing forum posts to ensure no leftover data from previous tests
        ForumPost.objects.all().delete()
                
        # Create a user for authentication
        self.user = User.objects.create_user(
            username='testuser', password='password123', email='testuser@example.com'
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)        

        self.forum_post = ForumPost.objects.create(
            user=self.user, title='Test Post', content='This is a test post.', is_active=True
        )

        self.url = reverse('forumpost-list')  # URL for listing forum posts
        self.single_post_url = reverse('forumpost-detail', args=[self.forum_post.id])  # URL for a single forum post


    # Test retrieving a list of forum posts
    def test_list_forum_posts(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # Ensure there is exactly 1 post returned
        self.assertEqual(len(response.data['results']), 1)  # Ensure only 1 post is returned


    # Test retrieving a specific forum post
    def test_retrieve_forum_post(self):
        response = self.client.get(self.single_post_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.forum_post.id)


    # Test creating a forum post (user is automatically assigned via `perform_create`)
    def test_create_forum_post(self):
        data = {
            'title': 'New Test Post',
            'content': 'Content for the new post',
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.user.id)  # Ensure the correct user is assigned


    # Test creating a forum post without specifying the user
    def test_create_forum_post_without_user(self):
        data = {
            'title': 'Another Test Post',
            'content': 'This should be assigned to the logged-in user.',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.user.id)  # User should be set automatically


    # Test updating an existing forum post
    def test_update_forum_post(self):
        data = {
            'title': 'Updated Test Post',
            'content': 'Updated content for the test post.',
        }
        response = self.client.put(self.single_post_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Test Post')
        self.assertEqual(response.data['content'], 'Updated content for the test post.')


    # Test deleting a forum post
    def test_delete_forum_post(self):
        response = self.client.delete(self.single_post_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Ensure the post is deleted
        response = self.client.get(self.single_post_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    # Test toggling the 'is_active' status of a forum post
    def test_toggle_active(self):
        # Ensure the post is initially active
        self.assertTrue(self.forum_post.is_active)
        
        # Make the custom POST request to toggle the 'is_active' status
        response = self.client.post(f'{self.single_post_url}toggle_active/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_active'])  # The post should now be inactive

        # Test again to toggle it back
        response = self.client.post(f'{self.single_post_url}toggle_active/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_active'])  # The post should be active again


    # Test filtering by 'is_active' status
    def test_filter_is_active(self):
        ForumPost.objects.create(user=self.user, title='Inactive Post', content='This is an inactive post.', is_active=False)

        # Filter by active posts
        response = self.client.get(self.url, {'is_active': 'true'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only one active post should be returned
        self.assertEqual(response.data['results'][0]['is_active'], True)

        # Filter by inactive posts
        response = self.client.get(self.url, {'is_active': 'false'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only one inactive post should be returned
        self.assertEqual(response.data['results'][0]['is_active'], False)


    # Test invalid 'is_active' filter (non-boolean values)
    def test_invalid_is_active_filter(self):
        # Create some forum posts with different 'is_active' values
        ForumPost.objects.create(user=self.user, title='Test Post 1', content='This is an active post.', is_active=True)
        ForumPost.objects.create(user=self.user, title='Test Post 2', content='This is an inactive post.', is_active=False)

        # Try filtering with an invalid 'is_active' value (e.g., 'invalid')
        response = self.client.get(self.url, {'is_active': 'invalid'})
        
        # The response should be 400 Bad Request due to invalid filter
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check that the error message is in the response
        error_message = "is_active must be a valid boolean (1 or 0, or 'true'/'false')."
        
        # Assert that the exact error message is in the response data
        self.assertIn(error_message, str(response.data))  # Convert the response.data to string and check for the error message



class CommentViewSetTests(TestCase):

    def setUp(self):
        Comment.objects.all().delete()
        ForumPost.objects.all().delete()

        self.user = User.objects.create_user(username='commenter', password='pass123', email='commenter@test.com')
        self.other_user = User.objects.create_user(username='someone_else', password='pass456', email='other@test.com')

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.post = ForumPost.objects.create(user=self.user, title='Post Title', content='Post Content', is_active=True)

        self.comment = Comment.objects.create(user=self.user, post=self.post, content='Initial comment', is_active=True)

        self.url = reverse('comment-list')
        self.detail_url = reverse('comment-detail', args=[self.comment.id])
        self.toggle_url = reverse('comment-toggle-active', args=[self.comment.id])


    def test_list_comments(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)


    def test_retrieve_comment(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.comment.id)


    def test_create_comment_authenticated(self):
        data = {'post': self.post.id, 'content': 'Nice post!'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Nice post!')
        self.assertEqual(response.data['post'], self.post.id)
        self.assertEqual(response.data['user'], self.user.id)


    def test_create_comment_unauthenticated(self):
        self.client.logout()
        data = {'post': self.post.id, 'content': 'Should not work'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_create_comment_with_blank_content(self):
        data = {'post': self.post.id, 'content': '   '}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content', response.data)


    def test_update_comment(self):
        data = {'post': self.post.id, 'content': 'Updated comment'}
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Updated comment')


    def test_partial_update_comment(self):
        data = {'content': 'Partially updated'}
        response = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Partially updated')


    def test_delete_comment(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())


    def test_toggle_active_status(self):
        self.assertTrue(self.comment.is_active)

        response = self.client.post(self.toggle_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertFalse(self.comment.is_active)

        response = self.client.post(self.toggle_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_active)


    def test_filter_by_post(self):
        Comment.objects.create(user=self.user, post=self.post, content='Another comment')
        response = self.client.get(self.url, {'post': self.post.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(c['post'] == self.post.id for c in response.data['results']))


    def test_filter_by_is_active(self):
        Comment.objects.create(user=self.user, post=self.post, content='Hidden comment', is_active=False)

        response_active = self.client.get(self.url, {'is_active': 'true'})
        self.assertEqual(response_active.status_code, status.HTTP_200_OK)
        self.assertTrue(all(c['is_active'] is True for c in response_active.data['results']))

        response_inactive = self.client.get(self.url, {'is_active': 'false'})
        self.assertEqual(response_inactive.status_code, status.HTTP_200_OK)
        self.assertTrue(all(c['is_active'] is False for c in response_inactive.data['results']))


    def test_invalid_is_active_filter(self):
        response = self.client.get(self.url, {'is_active': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
        "`is_active` must be a valid boolean value: true/false or 1/0.",
        str(response.data)
        )   



class ChallengeViewSetTests(TestCase):

    def setUp(self):
        Challenge.objects.all().delete()

        self.user = User.objects.create_user(username='tester', password='pass123', email='tester@test.com')
        self.other_user = User.objects.create_user(username='other', password='pass456', email='other@test.com')

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.now = timezone.now()
        self.challenge = Challenge.objects.create(
            name="Test Challenge",
            description="A challenge for testing",
            start_date=self.now + timedelta(days=1),
            end_date=self.now + timedelta(days=10),
            is_active=True
        )
        self.challenge.participants.add(self.user)

        self.url = reverse('challenge-list')
        self.detail_url = reverse('challenge-detail', args=[self.challenge.id])
        self.join_url = reverse('challenge-join', args=[self.challenge.id])
        self.leave_url = reverse('challenge-leave', args=[self.challenge.id])


    def test_list_challenges(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)


    def test_retrieve_challenge(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.challenge.id)


    def test_create_challenge(self):
        data = {
            "name": "New Challenge",
            "description": "Something cool",
            "start_date": (self.now + timedelta(days=2)).isoformat(),
            "end_date": (self.now + timedelta(days=5)).isoformat(),
            "is_active": True
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "New Challenge")


    def test_create_invalid_date_range(self):
        data = {
            "name": "Invalid Dates",
            "description": "Bad range",
            "start_date": (self.now + timedelta(days=5)).isoformat(),
            "end_date": (self.now + timedelta(days=2)).isoformat(),
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("End date cannot be earlier", str(response.data))


    def test_update_challenge(self):
        data = {
            "name": "Updated Name",
            "description": self.challenge.description,
            "start_date": self.challenge.start_date,
            "end_date": self.challenge.end_date,
            "is_active": False
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Updated Name")
        self.assertFalse(response.data['is_active'])


    def test_delete_challenge(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Challenge.objects.filter(id=self.challenge.id).exists())


    def test_filter_is_active(self):
        Challenge.objects.create(
            name="Inactive Challenge",
            description="Off",
            start_date=self.now,
            end_date=self.now + timedelta(days=3),
            is_active=False
        )
        response = self.client.get(self.url, {'is_active': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertTrue(all(c['is_active'] for c in response.data['results']))

        response = self.client.get(self.url, {'is_active': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertTrue(all(not c['is_active'] for c in response.data['results']))


    def test_join_challenge(self):
        self.challenge.participants.remove(self.user)
        response = self.client.post(self.join_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.user, self.challenge.participants.all())


    def test_join_already_joined(self):
        response = self.client.post(self.join_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Already joined.")


    def test_leave_challenge(self):
        response = self.client.post(self.leave_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.user, self.challenge.participants.all())


    def test_leave_not_joined(self):
        self.challenge.participants.remove(self.user)
        response = self.client.post(self.leave_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "You are not a participant.")


    def test_unauthenticated_cannot_create(self):
        self.client.logout()
        data = {
            "name": "Unauthorized Challenge",
            "description": "Should fail",
            "start_date": (self.now + timedelta(days=1)).isoformat(),
            "end_date": (self.now + timedelta(days=2)).isoformat()
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_unauthenticated_cannot_join_or_leave(self):
        self.client.logout()
        response = self.client.post(self.join_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(self.leave_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
