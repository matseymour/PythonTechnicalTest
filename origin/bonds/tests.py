from datetime import datetime

from django.urls import reverse
from factory_djoy import UserFactory
from rest_framework.test import APISimpleTestCase, APITestCase

from bonds.models import Bond


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


class BondTest(APITestCase):

    bond_count = 0

    def setUp(self):
        self.url = reverse('bond-list')
        self.user = UserFactory()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')

    @classmethod
    def _get_dummy_bond_data(cls):
        cls.bond_count += 1
        return {
            "isin": f"FR{cls.bond_count:010d}", "currency": "EUR",
            "size": 100000000, "maturity": datetime.now().strftime("%Y-%m-%d"),
            "lei": "R0MUWSFPU8MPRO8K5P83"
        }


class GetBondsTest(BondTest):

    @classmethod
    def _create_bond(cls, user):
        """
        Creates a test bond with the given user as the owner and a unique isin value
        :param user: A User model object instance
        :return: The newly created Bond model object instance
        """
        return Bond.objects.create(owner=user, **cls._get_dummy_bond_data())

    def test_get_all(self):

        # Create a couple of bonds in the DB for the user who will query
        owned_bond1, owned_bond2 = self._create_bond(self.user), self._create_bond(self.user)
        # Create another bond in the DB for some other user
        self._create_bond(UserFactory())

        resp = self.client.get(self.url)

        self.assertEqual(200, resp.status_code)
        data = resp.json()['results']
        # Check we only got the 2 bonds that the user who made the request owns
        self.assertEqual(2, len(data))
        self.assertNotEqual(data[0]['isin'], data[1]['isin'])
        owned_bond_isins = [owned_bond1.isin, owned_bond2.isin]
        self.assertIn(data[0]['isin'], owned_bond_isins)
        self.assertIn(data[1]['isin'], owned_bond_isins)

    def test_get_with_valid_filter(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')
        owned_bond1, _ = self._create_bond(self.user), self._create_bond(self.user)

        resp = self.client.get(f'{self.url}?isin={owned_bond1.isin}')

        self.assertEqual(200, resp.status_code)
        data = resp.json()['results']
        self.assertEqual(1, len(data))

    def test_get_with_invalid_filter(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')
        self._create_bond(self.user), self._create_bond(self.user)

        resp = self.client.get(f'{self.url}?foo=bar')

        self.assertEqual(200, resp.status_code)
        data = resp.json()['results']
        self.assertEqual(2, len(data))


class CreateBondTest(BondTest):

    def setUp(self):
        super(CreateBondTest, self).setUp()
        self.user = UserFactory()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')

    def test_successful(self):

        new_bond_data = self._get_dummy_bond_data()

        resp = self.client.post(self.url, data=new_bond_data)

        self.assertEqual(201, resp.status_code)
        bond_obj = Bond.objects.get(isin=resp.json()['isin'])
        self.assertEqual(self.user, bond_obj.owner)
        self.assertEqual(new_bond_data['maturity'], bond_obj.maturity.strftime("%Y-%m-%d"))
        for field in ['isin', 'size', 'currency', 'lei']:
            self.assertEqual(new_bond_data[field], getattr(bond_obj, field))

    def test_fields_missing(self):

        new_bond_data = {}

        resp = self.client.post(self.url, data=new_bond_data)

        self.assertEqual(400, resp.status_code)
        self.assertEqual({
            'isin': ['This field is required.'], 'size': ['This field is required.'],
            'currency': ['This field is required.'], 'maturity': ['This field is required.'],
            'lei': ['This field is required.']
        }, resp.json())

    def test_fields_blank(self):

        new_bond_data = {'isin': '', 'size': '', 'currency': '', 'maturity': '', 'lei': ''}

        resp = self.client.post(self.url, data=new_bond_data)

        self.assertEqual(400, resp.status_code)
        self.assertEqual({
            'isin': ['This field may not be blank.'], 'size': ['A valid integer is required.'],
            'currency': ['This field may not be blank.'],
            'maturity': ['Date has wrong format. Use one of these formats instead: YYYY-MM-DD.'],
            'lei': ['This field may not be blank.']
        }, resp.json())

    def test_fields_too_long(self):

        new_bond_data = {'size': 10000000, 'maturity': datetime.now().strftime('%Y-%m-%d')}
        for field in ['isin', 'lei', 'currency']:
            new_bond_data[field] = 'a' * (Bond._meta.get_field(field).max_length + 1)
        resp = self.client.post(self.url, data=new_bond_data)
        self.assertEqual(400, resp.status_code)
        self.assertEqual({
            'isin': ['Ensure this field has no more than 12 characters.'],
            'currency': ['Ensure this field has no more than 3 characters.'],
            'lei': ['Ensure this field has no more than 20 characters.']
        }, resp.json())
