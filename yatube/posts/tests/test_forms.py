from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post

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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Тестовый пост 2',
            'group': PostCreateFormTests.group.pk,
            'image': uploaded,
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

        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                image__isnull=False
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

    def test_create_comment_for_auth_user(self):
        """
        Валидная форма создает запись в Comment
        (для авторизованного пользователя).
        """

        form_data = {
            'text': 'Это тестовый комментарий!',
        }

        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostCreateFormTests.post.pk}
            ),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Проверяем, что коммент создан
        self.assertTrue(
            Comment.objects.filter(
                post__pk=PostCreateFormTests.post.pk,
                text=form_data['text'],
            ).exists()
        )

    def test_create_comment_for_unauth_user(self):
        """
        Проверяем, что неавторизованный пользователь
        не может создать комментарий.
        """

        form_data = {
            'text': 'Это тестовый комментарий!',
        }

        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostCreateFormTests.post.pk}
            ),
            data=form_data,
            follow=True
        )

        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{PostCreateFormTests.post.pk}/comment/'
        )

        # Проверяем, что коммент не создан
        self.assertFalse(
            Comment.objects.filter(
                post__pk=PostCreateFormTests.post.pk,
                text=form_data['text'],
            ).exists()
        )
