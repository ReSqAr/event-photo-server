import hashlib
import os
import tempfile

from PIL import Image
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

# Create your tests here.
from wphotos.models import Event, UserAuthenticatedForEvent, Photo, Like


class ApiTest(APITestCase):
    def setUp(self):
        # test photo
        image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'media/test_heart.jpg')

        # create user
        admin1 = User.objects.create_superuser('admin1', '', 'abc123abc', first_name='admin1')
        admin2 = User.objects.create_superuser('admin2', '', 'abc123abc', first_name='admin2')
        admin3 = User.objects.create_superuser('admin3', '', 'abc123abc', first_name='admin3')

        user1 = User.objects.create_user('user1', '', 'abc123abc', first_name='user1')
        user2 = User.objects.create_user('user2', '', 'abc123abc', first_name='user2')
        user3 = User.objects.create_user('user3', '', 'abc123abc', first_name='user3')

        # create events
        event1 = Event.objects.create(name='My Amazing Wedding 1',
                                      start_dt=timezone.now(),
                                      end_dt=timezone.now(),
                                      challenge='challenge',
                                      icon=image_path)
        event2 = Event.objects.create(name='My Amazing Wedding 2',
                                      start_dt=timezone.now(),
                                      end_dt=timezone.now(),
                                      challenge='challenge',
                                      icon=image_path)
        event3 = Event.objects.create(name='My Amazing Wedding 3',
                                      start_dt=timezone.now(),
                                      end_dt=timezone.now(),
                                      challenge='challenge',
                                      icon=image_path)

        # create authorisations
        auth31 = UserAuthenticatedForEvent.objects.create(user=user3, event=event1)
        auth32 = UserAuthenticatedForEvent.objects.create(user=user3, event=event2)
        auth33 = UserAuthenticatedForEvent.objects.create(user=user3, event=event3)

        # create photo
        photo31 = Photo.objects.create(
            owner=user3,
            event=event1,
            photo=image_path,
            visible=True,
            hash_md5='6f96ecc6e845a7a3838d83497133ba3d',
            comment='abc',
        )
        photo32 = Photo.objects.create(
            owner=user3,
            event=event2,
            photo=image_path,
            visible=True,
            hash_md5='6f96ecc6e845a7a3838d83497133ba3d',
            comment='abc',
        )
        photo33 = Photo.objects.create(
            owner=user3,
            event=event3,
            photo=image_path,
            visible=True,
            hash_md5='6f96ecc6e845a7a3838d83497133ba3d',
            comment='abc',
        )

    def test_create_user_via_api_too_short(self):
        initial_user_count = User.objects.count()

        url = reverse('create-user')
        data = {'name': 'a'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(User.objects.count(), initial_user_count)

    def test_create_user_via_api(self):
        initial_user_count = User.objects.count()

        name = 'abc'
        url = reverse('create-user')
        data = {'name': name}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(User.objects.count(), initial_user_count + 1)
        self.assertEqual(User.objects.last().first_name, name)

    def test_user_event_creation_fails(self):
        initial_event_count = Event.objects.count()

        # get user
        user = User.objects.get(username='user1')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.auth_token.key)

        # create event using admin
        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)

        url = reverse('event-list')
        event_data = {
            'name': 'My Amazing Wedding 4',
            'challenge': 'A123',
            'start_dt': '2016-12-31T23:59:00Z',
            'end_dt': '2017-12-31T23:59:00Z',
            'icon': tmp_file,
        }
        response = self.client.post(url, event_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Event.objects.count(), initial_event_count)

    def test_admin_event_list(self):
        initial_event_count = Event.objects.count()

        # get admin
        admin = User.objects.get(username='admin1')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + admin.auth_token.key)

        url = reverse('event-names')
        response = self.client.get(url, format='json')

        self.assertEqual(len(response.data), initial_event_count)

    def test_admin_event_creation(self):
        initial_event_count = Event.objects.count()

        # get admin
        admin = User.objects.get(username='admin1')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + admin.auth_token.key)

        # create event using admin
        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)

        url = reverse('event-list')
        event_data = {
            'name': 'My Amazing Wedding 4',
            'challenge': 'A123',
            'start_dt': '2016-12-31T23:59:00Z',
            'end_dt': '2017-12-31T23:59:00Z',
            'icon': tmp_file,
        }
        response = self.client.post(url, event_data, format='multipart')
        event_id = response.data['id']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Event.objects.count(), initial_event_count + 1)
        self.assertEqual(Event.objects.last().name, event_data['name'])
        self.assertEqual(Event.objects.last().challenge, event_data['challenge'])

    def test_auth_for_event_no_user(self):
        initial_auth_count = UserAuthenticatedForEvent.objects.count()

        # get event
        event = Event.objects.get(name='My Amazing Wedding 1')

        # auth
        challenge_for_user = '{username}${token}${challenge}'.format(
            username='',
            token='',
            challenge=event.challenge.strip().lower()
        )
        hashed_challenge = hashlib.md5(challenge_for_user.encode('utf8')).hexdigest()

        url = reverse('auth-user-for-event', kwargs={'event_id': event.id})
        data = {'hashed_challenge': hashed_challenge}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(UserAuthenticatedForEvent.objects.count(), initial_auth_count)

    def test_auth_for_event_failing_challenge(self):
        initial_auth_count = UserAuthenticatedForEvent.objects.count()

        # get user
        user = User.objects.get(username='user1')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.auth_token.key)

        # get event
        event = Event.objects.get(name='My Amazing Wedding 1')

        # auth
        challenge_for_user = '{username}${token}${challenge}'.format(
            username=user.first_name,
            token=user.auth_token.key,
            challenge=event.challenge.strip().lower()
        )
        hashed_challenge = hashlib.md5(challenge_for_user.encode('utf8')).hexdigest()
        # mistake!
        hashed_challenge += '?'

        url = reverse('auth-user-for-event', kwargs={'event_id': event.id})
        data = {'hashed_challenge': hashed_challenge}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(UserAuthenticatedForEvent.objects.count(), initial_auth_count)

    def test_auth_for_event(self):
        initial_auth_count = UserAuthenticatedForEvent.objects.count()

        # get user
        user = User.objects.get(username='user1')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.auth_token.key)

        # get event
        event = Event.objects.get(name='My Amazing Wedding 1')

        # auth
        challenge_for_user = '{username}${token}${challenge}'.format(
            username=user.first_name,
            token=user.auth_token.key,
            challenge=event.challenge.strip().lower()
        )
        hashed_challenge = hashlib.md5(challenge_for_user.encode('utf8')).hexdigest()

        url = reverse('auth-user-for-event', kwargs={'event_id': event.id})
        data = {'hashed_challenge': hashed_challenge}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserAuthenticatedForEvent.objects.count(), initial_auth_count + 1)
        self.assertEqual(response.data['name'], event.name)

    def test_upload_photo_no_auth(self):
        initial_photo_count = Photo.objects.count()

        # get user
        user = User.objects.get(username='user1')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.auth_token.key)

        # get event
        event = Event.objects.get(name='My Amazing Wedding 1')

        # try to upload photo (fails)
        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)

        url = reverse('photo-list')
        photo_data = {
            'event': event.id,
            'visible': True,
            'photo': tmp_file,
            'hash_md5': 'c',
            'comment': 'abc',
        }
        response = self.client.post(url, photo_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Photo.objects.count(), initial_photo_count)

    def test_upload_photo_wrong_md5(self):
        initial_photo_count = Photo.objects.count()

        # get user
        user = User.objects.get(username='user3')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.auth_token.key)

        # get event
        event = Event.objects.get(name='My Amazing Wedding 3')

        # try to upload photo (fails)
        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)

        url = reverse('photo-list')
        photo_data = {
            'event': event.id,
            'visible': True,
            'photo': tmp_file,
            'hash_md5': 'c',
            'comment': 'abc',
        }
        response = self.client.post(url, photo_data, format='multipart')

        print(response.data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Photo.objects.count(), initial_photo_count)

    def test_upload_photo(self):
        initial_photo_count = Photo.objects.count()

        # get user
        user = User.objects.get(username='user3')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.auth_token.key)

        # get event
        event = Event.objects.get(name='My Amazing Wedding 3')

        # try to upload photo (fails)
        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)

        url = reverse('photo-list')
        photo_data = {
            'event': event.id,
            'visible': True,
            'photo': tmp_file,
            'hash_md5': '78ef68043f5aed0de916c936e3d8fb2f',
            'comment': 'abc',
        }
        response = self.client.post(url, photo_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Photo.objects.count(), initial_photo_count + 1)
        self.assertEqual(response.data['comment'], photo_data['comment'])

    def test_list_photos_no_user(self):
        url = reverse('photo-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_list_photos_no_auth(self):
        # get user
        user = User.objects.get(username='user1')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.auth_token.key)

        url = reverse('photo-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_list_photos_owner(self):
        # get user
        user = User.objects.get(username='user3')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.auth_token.key)

        url = reverse('photo-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_list_photos_sort_order(self):
        # get user
        user1 = User.objects.get(username='user1')
        user2 = User.objects.get(username='user2')
        user3 = User.objects.get(username='user3')

        # get event
        event1 = Event.objects.get(name='My Amazing Wedding 1')
        event2 = Event.objects.get(name='My Amazing Wedding 2')
        event3 = Event.objects.get(name='My Amazing Wedding 3')

        # create auth
        UserAuthenticatedForEvent.objects.create(user=user1, event=event3)
        UserAuthenticatedForEvent.objects.create(user=user2, event=event2)
        UserAuthenticatedForEvent.objects.create(user=user2, event=event3)

        # get photos
        photo3, photo2, photo1 = Photo.objects.all()
        print(photo1.pk, photo2.pk, photo3.pk)

        # create likes
        Like.objects.create(owner=user1, photo=photo3)
        Like.objects.create(owner=user2, photo=photo2)
        Like.objects.create(owner=user2, photo=photo3)
        Like.objects.create(owner=user3, photo=photo1)
        Like.objects.create(owner=user3, photo=photo2)
        Like.objects.create(owner=user3, photo=photo3)

        # request
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user3.auth_token.key)
        url = reverse('photo-list')
        url += '?sort_order=likes'
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

        p1, p2, p3 = response.data['results']

        self.assertEqual(p1['likes'], 3)
        self.assertEqual(p2['likes'], 2)
        self.assertEqual(p3['likes'], 1)

    def test_list_photos_user_with_auth(self):
        # get user
        user = User.objects.get(username='user1')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.auth_token.key)

        # get event
        event2 = Event.objects.get(name='My Amazing Wedding 2')

        # create auth
        UserAuthenticatedForEvent.objects.create(user=user, event=event2)

        url = reverse('photo-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_like_no_user(self):
        initial_like_count = Like.objects.count()

        # get photo
        photo = Photo.objects.first()

        url = reverse('like-list')
        photo_data = {
            'photo': photo.id,
        }
        response = self.client.post(url, photo_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Like.objects.count(), initial_like_count)

    def test_like_no_auth(self):
        initial_like_count = Like.objects.count()

        # get user
        user = User.objects.get(username='user1')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.auth_token.key)

        # get photo
        photo = Photo.objects.first()

        url = reverse('like-list')
        photo_data = {
            'photo': photo.id,
        }
        response = self.client.post(url, photo_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Like.objects.count(), initial_like_count)

    def test_like(self):
        initial_like_count = Like.objects.count()

        # get user
        user = User.objects.get(username='user3')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.auth_token.key)

        # get photo
        photo = Photo.objects.first()

        url = reverse('like-list')
        photo_data = {
            'photo': photo.id,
        }
        response = self.client.post(url, photo_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Like.objects.count(), initial_like_count + 1)

        # check photo liked_by_current_user
        url = reverse('photo-detail', kwargs={'pk': photo.pk})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['liked_by_current_user'], True)

    def test_like_not_owner(self):
        initial_like_count = Like.objects.count()

        # get user
        user = User.objects.get(username='user1')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.auth_token.key)

        # get photo
        photo = Photo.objects.first()

        # create auth
        UserAuthenticatedForEvent.objects.create(user=user, event=photo.event)

        url = reverse('like-list')
        photo_data = {
            'photo': photo.id,
        }
        response = self.client.post(url, photo_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Like.objects.count(), initial_like_count + 1)

        # check photo liked_by_current_user
        url = reverse('photo-detail', kwargs={'pk': photo.pk})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['liked_by_current_user'], True)

        # get other user
        user = User.objects.get(username='user3')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.auth_token.key)

        # check photo liked_by_current_user
        url = reverse('photo-detail', kwargs={'pk': photo.pk})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['liked_by_current_user'], False)
