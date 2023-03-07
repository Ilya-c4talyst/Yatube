from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, в котором больше 15 символов',
        )

    def test_model_post_have_correct_object_names(self):
        """Проверяем, что у моделеи Post корректно работает __str__."""
        post = PostModelTest.post
        text = post.text[:15]
        self.assertEqual(text, str(post))

    def test_model_group_have_correct_object_names(self):
        """Проверяем, что у моделеи Group корректно работает __str__."""
        group = PostModelTest.group
        title = group.title
        self.assertEqual(title, str(PostModelTest.group))

    def test_models_have_correct_verbose(self):
        """Проверяем наличие у моделей verbose_name и help_text"""
        test = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'author': 'Автор',
            'group': 'Группа',
            'pub_date': 'Дата публикации',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    test._meta.get_field(field).verbose_name, expected_value)

    def test_models_have_correct_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        task = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    task._meta.get_field(field).help_text, expected_value)
