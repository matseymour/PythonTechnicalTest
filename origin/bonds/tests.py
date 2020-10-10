from django.urls import reverse
from factory_djoy import UserFactory
from rest_framework.test import APISimpleTestCase, APITestCase


class HelloWorld(APISimpleTestCase):
    def test_root(self):
        resp = self.client.get("/")
        assert resp.status_code == 200


class AuthenticateTest(APITestCase):

    def setUp(self):
        self.url = reverse('authenticate')

    def test_valid_credentials(self):
        username, password = 'mat', 'pa55word'
        UserFactory(username=username, password=password)

        resp = self.client.post(self.url, data={'username': username, 'password': password})

        self.assertEqual(200, resp.status_code)
        self.assertIn('token', resp.json())

    def test_unknown_credentials(self):
        resp = self.client.post(self.url, data={'username': "foo", 'password': "bar"})

        self.assertEqual(400, resp.status_code)
