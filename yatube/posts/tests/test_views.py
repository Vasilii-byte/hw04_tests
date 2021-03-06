from http import HTTPStatus

from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
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

        # генерим несколько постов для проверки работы пажинатора
        POSTS_COUNT: int = 17
        posts_for_create = []
        for i in range(POSTS_COUNT):
            # для 12-го поста задаем другого автора и отсутствие группы
            if i == 12:
                group = None
                author = cls.user_not_author
            else:
                group = cls.group
                author = cls.user

            posts_for_create.append(
                Post(
                    author=author,
                    text=f'Тестовый пост {i}',
                    group=group,
                    image=uploaded
                )
            )
        Post.objects.bulk_create(posts_for_create)

        cls.POST_ID_FOR_TEST = 1

        cls.comment = Comment.objects.create(
            post=Post.objects.get(pk=cls.POST_ID_FOR_TEST),
            author=cls.user,
            text='Это тестовый комментарий'
        )

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(
            PostPagesTests.user_not_author
        )

    def test_pages_uses_correct_template_for_auth_user(self):
        """
        URL-адрес использует соответствующий шаблон
        (для авторизованного пользователя).
        """
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': 'APushkin'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.POST_ID_FOR_TEST}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostPagesTests.POST_ID_FOR_TEST}
            ): 'posts/create_post.html',

            reverse('posts:post_create'): 'posts/create_post.html'
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_uses_correct_template_for_unauth_user(self):
        """
        URL-адрес использует соответствующий шаблон
        (для неавторизованного пользователя).
        """
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': 'APushkin'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.POST_ID_FOR_TEST}
            ): 'posts/post_detail.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        text_0 = first_object.text
        author_0 = first_object.author.username
        group_0 = first_object.group.title

        self.assertEqual(author_0, 'APushkin')
        self.assertEqual(text_0, 'Тестовый пост 16')
        self.assertEqual(group_0, 'Тестовая группа')
        self.assertIsNotNone(first_object.image)

    def test_post_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        text_0 = first_object.text
        author_0 = first_object.author.username
        group_0 = first_object.group.title
        self.assertEqual(author_0, 'APushkin')
        self.assertEqual(text_0, 'Тестовый пост 16')
        self.assertEqual(group_0, 'Тестовая группа')
        self.assertIsNotNone(first_object.image)

    def test_post_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'APushkin'})
        )
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        text_0 = first_object.text
        author_0 = first_object.author.username
        group_0 = first_object.group.title
        self.assertEqual(author_0, 'APushkin')
        self.assertEqual(text_0, 'Тестовый пост 16')
        self.assertEqual(group_0, 'Тестовая группа')
        self.assertIsNotNone(first_object.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.POST_ID_FOR_TEST}
            )
        )
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['post']
        text_0 = first_object.text
        author_0 = first_object.author.username
        group_0 = first_object.group.title
        self.assertEqual(author_0, 'APushkin')
        self.assertEqual(text_0, 'Тестовый пост 0')
        self.assertEqual(group_0, 'Тестовая группа')
        self.assertIsNotNone(first_object.image)

    def test_post_edit_show_correct_context(self):
        """Шаблон create_post при редактировании сформирован
        с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostPagesTests.POST_ID_FOR_TEST}
            )
        )
        is_edit = response.context.get('is_edit')
        self.assertTrue(is_edit)

    def test_post_create_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        is_edit = response.context.get('is_edit')
        self.assertFalse(is_edit)

    def test_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

        response = self.guest_client.get(
            reverse(
                'posts:profile', kwargs={'username': 'APushkin'}
            )
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_seven_records(self):
        """Проверка: количество постов на первой странице равно 7 (6)."""
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 7)

        response = self.guest_client.get(
            reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 6)

        response = self.guest_client.get(
            reverse(
                'posts:profile', kwargs={'username': 'APushkin'}
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 6)

    def test_page_edit_form_show_correct_context(self):
        """Шаблон редактирования поста сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostPagesTests.POST_ID_FOR_TEST}
            )
        )

        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_page_create_form_show_correct_context(self):
        """Шаблон создания поста сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )

        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_comment_is_on_page(self):
        """Проверка: Комментарий есть на странице."""
        response = self.guest_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.POST_ID_FOR_TEST}
            ),
        )
        self.assertEqual(len(response.context['comments']), 1)

    def test_cache_page(self):
        """ Проверка: количество постов на странице
        после удаления поста не изменилось."""
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        content_before = response.content

        post = Post.objects.get(pk=PostPagesTests.POST_ID_FOR_TEST)
        post.delete()

        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(content_before, response.content)

        cache.clear()
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertNotEqual(content_before, response.content)

    def test_auth_user_can_follow(self):
        """Авторизованный пользователь может подписаться и отписаться."""
        author = User.objects.create_user(username='Lermontov')
        Post.objects.create(
            author=author,
            text='Тестовый пост для проверки подписки'
        )

        # создаем подписку
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': author.username}
            )
        )
        # проверяем добавление подписки в базу
        self.assertTrue(
            Follow.objects.filter(
                user=PostPagesTests.user, author=author
            ).exists()
        )

        # проверяем, что пост автора добавился на страницу пользователя
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(response.context['page_obj'][0].author, author)

        # проверяем возможности отписки
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': author.username}
            )
        )

        self.assertFalse(
            Follow.objects.filter(
                user=PostPagesTests.user, author=author
            ).exists()
        )

    def test_unauth_user_can_follow(self):
        """Неавторизованный пользователь не может подписаться и отписаться."""
        author = User.objects.create_user(username='Lermontov')
        Post.objects.create(
            author=author,
            text='Тестовый пост для проверки подписки'
        )

        # проверяем подписку
        response = self.guest_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': author.username}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            (f'/auth/login/?next=/profile/{author.username}/follow/')
        )
        self.assertFalse(
            Follow.objects.filter(
                user=PostPagesTests.user, author=author
            ).exists()
        )

        # проверяем, что пост автора отсутствует на странице пользователя
        response = self.authorized_client_not_author.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response.context['page_obj']), 0)

        # проверяем возможности отписки
        response = self.guest_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': author.username}
            )
        )
        self.assertRedirects(
            response,
            (f'/auth/login/?next=/profile/{author.username}/unfollow/')
        )
