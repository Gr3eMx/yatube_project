from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Group, Post
from django.urls import reverse

User = get_user_model()


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


    def setUp(self):
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(PostCreateFormTests.user)

    def test_create_task(self):
        """Валидная форма создает запись в Post."""
        tasks_count = Post.objects.count()
        form = {
            'text': PostCreateFormTests.post.text,
            'group': PostCreateFormTests.post.group.id,
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
                'post_id':PostCreateFormTests.post.id}),
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