from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='APushkin')
        cls.user_not_author = User.objects.create_user(username='Turgenev')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )

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
            '/',
            f'/group/{StaticURLTests.group.slug}/',
            f'/profile/{StaticURLTests.user.username}/',
            f'/posts/{StaticURLTests.post.pk}/',
        )
        for url in http_addresses:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_return_status_ok_in_post_edit_for_author(self):
        """Проверка возможности редактирования поста для автора поста."""
        response = self.authorized_client.get(
            f'/posts/{StaticURLTests.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_return_redirect_in_post_edit_for_not_author(self):
        """Проверка редиректа с /edit/ для авторизованного пользователя,
        который не является автором.
        """
        response = self.authorized_client_not_author.get(
            f'/posts/{StaticURLTests.post.pk}/edit/'
        )
        self.assertRedirects(
            response,
            (f'/posts/{StaticURLTests.post.pk}/')
        )

    def test_return_redirect_in_post_edit_for_unauth_user(self):
        """Проверка редиректа с /create/ для гостя."""
        response = self.guest_client.get(
            f'/posts/{StaticURLTests.post.pk}/edit/'
        )
        self.assertRedirects(
            response,
            (f'/auth/login/?next=/posts/{StaticURLTests.post.pk}/edit/')
        )

    def test_return_status_ok_for_create_for_auth_user(self):
        """Проверка создания поста для авторизованного пользователя."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_return_redirect_in_create_unuth_user(self):
        """Проверка редиректа с /create/ для гостя."""
        response = self.guest_client.get('/create/')
        self.assertRedirects(
            response,
            ('/auth/login/?next=/create/')
        )

    def test_return_status_not_found(self):
        """Проверка возврата статуса Страница не найдена."""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """Проверка вызываемых шаблонов для каждого адреса."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{StaticURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{StaticURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{StaticURLTests.post.pk}/': 'posts/post_detail.html',
            f'/posts/{StaticURLTests.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
