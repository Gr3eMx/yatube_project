import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from posts.models import Group, Post
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Первая группа',
            slug='test_slug',
            description='Тестовое описание первой группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(PostCreateFormTests.user)

    def test_create_task(self):
        """Валидная форма создает запись в Post."""
        tasks_count = Post.objects.count()
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
        form = {
            'text': PostCreateFormTests.post.text,
            'group': PostCreateFormTests.post.group.id,
            'image': uploaded

        }
        response = self.authorized_client_author.post(
            reverse('posts:post_create'),
            data=form,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={
                'username': PostCreateFormTests.user})
                             )
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=PostCreateFormTests.post.group,
                text=PostCreateFormTests.post.text,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        """Валидация редактирование поста и сохранение его в БД."""
        tasks_count = Post.objects.count()
        form = {
            'text': 'Измененный текст',
            'group': PostCreateFormTests.post.group.id,
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_edit', kwargs={
                'post_id': PostCreateFormTests.post.id}),
            data=form, follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                group=PostCreateFormTests.post.group,
                text=form['text'],
            ).exists()
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={
                'post_id': PostCreateFormTests.post.id})
                             )
        self.assertEqual(Post.objects.count(), tasks_count)
