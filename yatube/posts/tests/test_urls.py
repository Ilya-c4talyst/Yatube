from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache


from posts.models import Post, Group, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Avtoritto')
        cls.group = Group.objects.create(
            title='Группа поддержки ментального здоровья после этой темы',
            slug='test',
            description='Я обязательно выживу',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Какой-то текст о том, как мне тяжело живётся',
        )
        cls.url_without_auth = {
            reverse('posts:index'):
            'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': cls.author.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': cls.post.id}):
            'posts/post_detail.html',
        }
        cls.url_with_auth = {
            reverse('posts:post_create'):
            'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': cls.post.id}):
            'posts/create_post.html',
            reverse('posts:follow_index'):
            'posts/follow.html',
        }
        cls.all_urls = {**cls.url_with_auth, **cls.url_without_auth}

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_urls_auth_not(self):
        """Страницы, для которых не нужна авторизация, работают корректно."""
        for url in StaticURLTests.url_without_auth:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_with_auth(self):
        """Страницы, для которых нужна авторизация, работают корректно."""
        for url in StaticURLTests.all_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        """Запрос к несуществующей странице вернёт ошибку 404."""
        response = self.guest_client.get('/imposter_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_post_urls_create_redirect_guest(self):
        """Редирект гостя со страницы post_create/edit."""
        urls = {
            'create_post_url':
            reverse('posts:post_create'),
            'post_edit_url':
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        }
        login_url = reverse('users:login')
        for url in urls.values():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(
                    response,
                    f'{login_url}?next={url}'
                )

    def test_edit_post_by_not_author(self):
        """Редирект для читателей постов."""
        self.user = User.objects.create_user(username='Somebody')
        self.authorized_client.force_login(self.user)
        post_edit_url = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id}
        )
        redirect_url = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        )
        response = self.authorized_client.get(post_edit_url)
        self.assertRedirects(
            response,
            redirect_url
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in self.all_urls.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
