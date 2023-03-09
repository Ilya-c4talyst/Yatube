import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, User, Group, Comment


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='group',
            slug='group',
            description='texttexttext'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create(username='Avtoritto')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Проверка валидации и создания записи в БД"""
        count_posts = Post.objects.count()
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
        new_form = {
            'text': 'Наверное, что-то очень важное',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=new_form,
            follow=True
        )
        post = Post.objects.get(pk=1)
        self.assertEqual(post.group, PostCreateForm.group)
        self.assertEqual(post.text, new_form['text'])
        self.assertRedirects(
            response, reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post(self):
        """Проверка валидации и изменения записи в БД."""
        post = Post.objects.create(
            author=self.user,
            text='Наверное, что-то не очень важное',
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
        count_posts = Post.objects.count()
        new_form = {
            'text': 'Наверное, что-то очень важное',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=new_form,
            follow=True
        )
        post = Post.objects.get(id=post.id)
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': post.id}
            )
        )
        self.assertEqual(post.text, new_form['text'])
        self.assertEqual(post.group, PostCreateForm.group)
        self.assertEqual(Post.objects.count(), count_posts)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        def test_posts_forms_comment_create_authorized_user(self):
            """Добавляется комментарий если пользователь авторизован."""
            post = Post.objects.create(
                text='Тестовый пост',
                author=self.user,
            )
            count_comments = Comment.objects.count()
            response = self.authorized_client.post(
                reverse(
                    'posts:add_comment',
                    kwargs={'post_id': post.pk}
                ),
                data={'text': 'Тестовый комментарий'},
                follow=True
            )
            comment = Comment.objects.get(pk=1)
            self.assertEqual(comment.text, 'Тестовый комментарий')
            self.assertEqual(Comment.objects.count(), count_comments + 1)
            self.assertRedirects(
                response,
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': post.pk}
                )
            )

    def test_posts_forms_comment_create_guest_user(self):
        """Неавторизованный пользователь не может добавить комментарий."""
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
        )
        count_comments = Comment.objects.count()
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.pk}
            ),
            data={'text': 'Тестовый комментарий'},
            follow=True
        )
        self.assertIsNone(Comment.objects.first())
        self.assertEqual(Comment.objects.count(), count_comments)
