from rest_framework.test import APIClient
from rest_framework import status

from django.test import TestCase
from django.urls import reverse

from community.models import ForumPost
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