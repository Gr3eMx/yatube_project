from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Group, Post
from http import HTTPStatus

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(PostURLTests.user)

    def test_urls_uses_correct_template(self):
        """Страницы доступна любому пользователю."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_url_on_authorized(self):
        """Страница /create/ редиректит на авторизацию."""
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_edit_on_author_of_post(self):
        """Страница /posts/<post_id>/edit/ редиректит на пост автора"""
        response = self.authorized_client.get(f'/posts/{PostURLTests.post.id}/edit/')
        self.assertRedirects(response, f'/posts/{PostURLTests.post.id}/')

    def test_urls_404_of_unexisting_page(self):
        """Страница не существует"""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_comments_post(self):
        """Неавторизованный пользователь не может комментировать."""
        post_id = PostURLTests.post.id
        response = self.guest_client.get(f'/posts/{post_id}/comment/')
        self.assertRedirects(response, f'/auth/login/?next=/posts/{post_id}/comment/')
