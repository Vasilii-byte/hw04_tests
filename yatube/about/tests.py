# Create your tests here.

from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='APushkin')
        cls.user_not_author = User.objects.create_user(username='Turgenev')

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticURLTests.user)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(
            StaticURLTests.user_not_author
        )

    def test_return_status_ok_for_unauth_user(self):
        """Проверка возврата статуса 200 для неавторизованных пользователей."""
        http_addresses = (
            '/about/author/',
            '/about/tech/',
        )
        for url in http_addresses:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
