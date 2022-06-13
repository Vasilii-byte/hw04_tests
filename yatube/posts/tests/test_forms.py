import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='APushkin')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post_for_auth_user(self):
        """
        Валидная форма создает запись в Post
        (для авторизованного пользователя).
        """
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Тестовый пост 2',
            'group': PostCreateFormTests.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'APushkin'})
        )

        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)

        # Проверяем, что создалась запись с заданным текстом
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
            ).exists()
        )

    def test_create_post_for_unauth_user(self):
        """
        Валидная форма создает запись в Post
        (для неавторизованного пользователя).
        """
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Тестовый пост 2',
            'group': PostCreateFormTests.group.pk,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            '/auth/login/?next=/create/'
        )

        # Проверяем, изменилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_post_for_auth_user(self):
        """
        Валидная форма редактирует запись в Post
        (для авторизованного пользователя).
        """
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Измененный пост 1',
            'group': PostCreateFormTests.group.pk
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostCreateFormTests.post.pk}
            ),
            data=form_data,
            follow=True
        )

        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostCreateFormTests.post.pk}
            )
        )

        # Проверяем, не изменилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)

        # Проверяем, что изменилась запись с заданным текстом
        self.assertTrue(
            Post.objects.filter(
                text='Измененный пост 1'
            ).exists()
        )

    def test_edit_post_for_unauth_user(self):
        """
        Валидная форма редактирует запись в Post
        (для неавторизованного пользователя).
        """
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Измененный пост 1',
            'group': PostCreateFormTests.group.pk
        }
        response = self.guest_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostCreateFormTests.post.pk}
            ),
            data=form_data,
            follow=True
        )

        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{PostCreateFormTests.post.pk}/edit/'
        )

        # Проверяем, не изменилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)

        # Проверяем, что не изменилась запись с заданным текстом
        self.assertFalse(
            Post.objects.filter(
                text='Измененный пост 1'
            ).exists()
        )
