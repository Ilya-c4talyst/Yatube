import tempfile
import shutil

from django import forms
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache


from posts.models import Post, Group, User, Follow, Comment
from posts.forms import PostForm, CommentForm


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Avtoritto')
        cls.group = Group.objects.create(
            title='Группа номер какая-то',
            slug='test',
            description='Всем привет, получается',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Какой-то текст о том, как мне тяжело живётся',
            group=cls.group,
            image=cls.uploaded
        )
        cls.list_urls = {
            'index': (
                'posts:index',
                'posts/index.html',
                {}
            ),
            'group_list': (
                'posts:group_list',
                'posts/group_list.html',
                {'slug': cls.group.slug}
            ),
            'profile': (
                'posts:profile',
                'posts/profile.html',
                {'username': cls.user.username}
            ),
            'post_detail': (
                'posts:post_detail',
                'posts/post_detail.html',
                {'post_id': cls.post.pk}
            ),
            'post_create': (
                'posts:post_create',
                'posts/create_post.html',
                {}
            ),
            'post_edit': (
                'posts:post_edit',
                'posts/create_post.html',
                {'post_id': cls.post.pk}
            ),
            'follow_index': (
                'posts:follow_index',
                'posts/follow.html',
                {}
            ),
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsViewsTests.user)
        cache.clear()

    def context_check(self, response):
        context = response.context
        if 'post' in context:
            post_object = context['post']
        elif 'post_obj' in context:
            post_object = context['page_obj'][0]
        context_objects = {
            self.user.id: post_object.author.id,
            self.post.text: post_object.text,
            self.group.slug: post_object.group.slug,
            self.post.id: post_object.id,
            self.post.image: post_object.image
        }
        for reverse_name, response_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)
        self.assertIsInstance(post_object, Post)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for touple in self.list_urls.values():
            (url, template, kwargs) = touple
            with self.subTest(template=template):
                response = self.authorized_client.get(
                    reverse(url, kwargs=kwargs)
                )
                self.assertTemplateUsed(response, template)

    def test_index_context(self):
        """Проверка контекста в index."""
        name_url, _, args = PostsViewsTests.list_urls['index']
        response = self.guest_client.get(reverse(name_url, kwargs=args))
        self.assertIsInstance(response.context['post'], Post)
        self.context_check(response)

    def test_index_page_cache(self):
        """Кеширование posts:index работатет."""
        response = self.authorized_client.get(reverse('posts:index'))
        page_content = response.content
        Post.objects.first().delete()
        response = self.authorized_client.get(reverse('posts:index'))
        cached_page_content = response.content
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        cleared_page_content = response.content
        self.assertEqual(page_content, cached_page_content)
        self.assertNotEqual(cached_page_content, cleared_page_content)

    def test_group_list_context(self):
        """Проверка контекста в group_list."""
        name_url, _, args = PostsViewsTests.list_urls['group_list']
        response = self.guest_client.get(
            reverse(name_url, kwargs=args)
        )
        self.context_check(response)
        self.assertEqual(response.context['group'], PostsViewsTests.group)

    def test_profile_context(self):
        """Проверка контекста в profile."""
        name_url, _, args = PostsViewsTests.list_urls['profile']
        response = self.guest_client.get(
            reverse(name_url, kwargs=args)
        )
        self.context_check(response)
        self.assertEqual(response.context['profile'], PostsViewsTests.user)
        self.assertFalse(response.context['following'])

    def test_post_detail_context(self):
        """Проверка контекста в post_detail."""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Комментарий',
        )
        name_url, _, args = PostsViewsTests.list_urls['post_detail']
        response = self.guest_client.get(
            reverse(name_url, kwargs=args)
        )
        form_fields = {
            'text': forms.fields.CharField,
        }
        form = response.context.get('form')
        self.assertIsInstance(form, CommentForm)
        self.assertIsInstance(form.fields['text'], form_fields['text'])
        self.context_check(response)
        self.assertEqual(response.context['comments'].first(), comment)

    def test_create_post_context(self):
        """Проверка контекста в create_post."""
        name_url, _, args = PostsViewsTests.list_urls['post_create']
        response = self.authorized_client.get(
            reverse(name_url, kwargs=args)
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for form, result in form_fields.items():
            with self.subTest(form=form):
                form_field = response.context.get('form')
                self.assertIsInstance(form_field, PostForm)
                self.assertIsInstance(form_field.fields[form], result)

    def test_post_edit_context(self):
        """Проверка контекста в post_edit."""
        name_url, _, args = PostsViewsTests.list_urls['post_edit']
        response = self.authorized_client.get(
            reverse(name_url, kwargs=args)
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for form, result in form_fields.items():
            with self.subTest(form=form):
                form_field = response.context.get('form')
                self.assertIsInstance(form_field, PostForm)
                self.assertIsInstance(form_field.fields[form], result)
        self.context_check(response)

    def test_check_group_is_not_empty(self):
        """Проверка создания поста"""
        test_post = Post.objects.create(
            author=self.user,
            text='Пробный текст',
            group=self.group)
        form_fields = {
            reverse('posts:index'):
            test_post,
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            test_post,
            reverse('posts:profile', kwargs={'username': self.post.author}):
            test_post,
        }
        for form, result in form_fields.items():
            with self.subTest(form=form):
                response = self.authorized_client.get(form)
                form_field = response.context['page_obj']
                self.assertIn(result, form_field)

    def test_check_group_have_correct_place(self):
        """Проверка принадлежности поста к нужной группе."""
        test_post = Post.objects.create(
            author=self.user,
            text='Пробный текст',
            group=self.group)
        test_group = Group.objects.create(
            title='Тест группа',
            slug='first',
            description='Всем привет',
        )
        name_url, _, args = PostsViewsTests.list_urls['group_list']
        response = self.authorized_client.get(reverse(name_url, kwargs=args))
        field = response.context['page_obj']
        self.assertIn(test_post, field)
        response = self.authorized_client.get(
            reverse(name_url, kwargs={'slug': test_group.slug})
        )
        field = response.context['page_obj']
        self.assertNotIn(test_post, field)

    def test_follow(self):
        """Авторизованный пользователь может подписаться на автора."""
        content_maker = User.objects.create_user(
            username='content_maker'
        )
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': content_maker}
            )
        )
        following = Follow.objects.first()
        self.assertEqual(following.author, content_maker)
        self.assertEqual(following.user, self.user)

    def test_posts_view_unfollow_authenticated(self):
        """Авторизованный пользователь может отписаться от автора."""
        content_maker = User.objects.create_user(
            username='content_maker'
        )
        Follow.objects.create(
            user=PostsViewsTests.user,
            author=content_maker
        )
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': content_maker}
            )
        )
        following = Follow.objects.filter(
            author=content_maker).exists()
        self.assertFalse(following)

    def test_posts_views_follow_correct_context(self):
        """Проверка контекста для follow_index."""
        Follow.objects.create(
            user=PostsViewsTests.user,
            author=PostsViewsTests.user
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.context_check(response)

    def unfollow_authors_is_not_in_page(self):
        """Пост не попадает к пользователям, не подписанным на автора."""
        new_post = Post.objects.create(
            author=self.user,
            text='Новая запись',
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(new_post, response)

    def test_paginator(self):
        """Проверка паджинатора."""
        Post.objects.all().delete
        FIRST_PAGE_AMOUNT = settings.PAGINATOR_COUNT_POSTS
        SECOND_PAGE_AMOUNT = 1
        posts_list = [
            Post(
                text=f'Постик под номером {i}',
                author=PostsViewsTests.user,
                group=PostsViewsTests.group
            ) for i in range(1, FIRST_PAGE_AMOUNT + SECOND_PAGE_AMOUNT)
        ]
        Post.objects.bulk_create(posts_list)
        pages_with_pagination = {
            'index': PostsViewsTests.list_urls['index'],
            'group_list': PostsViewsTests.list_urls['group_list'],
            'profile': PostsViewsTests.list_urls['profile']
        }
        for page in pages_with_pagination.values():
            name_url, _, args = page
            response = self.guest_client.get(reverse(name_url, kwargs=args))
            self.assertEqual(
                len(response.context['page_obj']),
                FIRST_PAGE_AMOUNT
            )
            response = self.guest_client.get(
                reverse(name_url, kwargs=args) + '?page=2'
            )
            self.assertEqual(
                len(response.context['page_obj']),
                SECOND_PAGE_AMOUNT
            )
