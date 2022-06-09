# Create your tests here.

from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.test import TestCase, Client
from django.urls import reverse

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
            '/auth/signup/',
            '/auth/logout/',
            '/auth/login/',
            '/auth/password_reset/',
        )
        for url in http_addresses:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_return_status_ok_for_auth_user(self):
        """Проверка возврата статуса 200 для авторизованных пользователей."""
        http_addresses = (
            '/auth/logout/',
            '/auth/password_reset/',
        )
        for url in http_addresses:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('users:signup'): 'users/signup.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        form_data = {
            'first_name': 'Name_first',
            'last_name': 'Name_last',
            'username': 'testname',
            'email': 'test@ya.ru',
            'password1': 'test123test',
            'password2': 'test123test',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

        user = get_object_or_404(User, username='testname')

        self.assertEqual(user.get_username(), 'testname')
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('posts:index')
        )

        # Проверяем, увеличилось ли число постов
        #self.assertEqual(Post.objects.count(), posts_count + 1)

        # Проверяем, что создалась запись с заданным текстом
        #self.assertTrue(
        #    Post.objects.filter(
        #        text='Тестовый пост 2'
        #    ).exists()
        #)
