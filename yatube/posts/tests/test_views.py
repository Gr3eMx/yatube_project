import shutil
import tempfile
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from posts.models import Post, Group, Comment, Follow
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostVIEWSTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group_1 = Group.objects.create(
            title='Тестовая группа один',
            slug='test_slug_1',
            description='Тестовое описание один',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа два',
            slug='test_slug_2',
            description='Тестовое описание два',
        )
        for i in range(6):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group_1,
            )
            cls.post.pub_date = timezone.now() + timedelta(minutes=i)
            cls.post.save()
        for i in range(6, 12):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group_2,
            )
            cls.post.pub_date = timezone.now() + timedelta(minutes=i)
            cls.post.save()

    def setUp(self):
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/group_list.html': (
                reverse('posts:group_posts', kwargs={
                    'slug': PostVIEWSTests.group_1.slug})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={
                    'username': PostVIEWSTests.user.username})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={
                    'post_id': PostVIEWSTests.post.id})
            ),
            'posts/create_post.html':
                reverse('posts:post_create'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def context_test(self, page_obj_id, response):
        post_result = Post.objects.get(
            text=f'Тестовый пост {11 - page_obj_id}'
        )
        post = response.context['page_obj'][page_obj_id]
        post_author = post.author.username
        post_text = post.text
        post_group = post.group
        post_id = post.id
        self.assertEqual(post_author, PostVIEWSTests.user.username)
        self.assertEqual(post_text, post_result.text)
        self.assertEqual(str(post_group), str(post_result.group))
        self.assertEqual(post_id, post_result.id)

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом.
        Проверяется вторая группа"""
        response = self.authorized_client_author.get(
            reverse('posts:group_posts', kwargs={
                'slug': PostVIEWSTests.group_2.slug
            }))
        first_obj_in_page = 0
        last_obj_in_page = 5
        self.context_test(first_obj_in_page, response)
        self.context_test(last_obj_in_page, response)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse('posts:profile', kwargs={
                'username': PostVIEWSTests.user.username
            }))
        first_obj_in_page = 0
        last_obj_in_page = 9
        self.context_test(first_obj_in_page, response)
        self.context_test(last_obj_in_page, response)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse('posts:post_detail', kwargs={
                'post_id': PostVIEWSTests.post.id
            }))
        post = response.context['post']
        post_result = Post.objects.get(id=f'{PostVIEWSTests.post.id}')
        post_author = post.author.username
        post_text = post.text
        post_group = post.group
        post_id = post.id
        self.assertEqual(post_author, PostVIEWSTests.user.username)
        self.assertEqual(post_text, post_result.text)
        self.assertEqual(str(post_group), str(post_result.group))
        self.assertEqual(post_id, post_result.id)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse('posts:post_edit', kwargs={
                'post_id': f'{PostVIEWSTests.post.id}'
            })
        )
        title_inital_text = response.context['form'].instance.text
        self.assertEqual(title_inital_text, PostVIEWSTests.post.text)

        title_inital_author = response.context['form'].instance.author
        self.assertEqual(str(title_inital_author), str(PostVIEWSTests.user.username))

    def test_home_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_in_3_page(self):
        """Проверка появления поста №1 на главной странице,
        странице группы2 и в профиле пользователя"""
        response_group = self.authorized_client_author.get(
            reverse('posts:group_posts', kwargs={
                'slug': f'{PostVIEWSTests.group_2.slug}'
            })
        )
        response_profile = self.authorized_client_author.get(
            reverse('posts:profile', kwargs={
                'username': f'{PostVIEWSTests.user.username}'
            })
        )
        first_obj_in_page = 0
        self.context_test(first_obj_in_page, response_group)
        self.context_test(first_obj_in_page, response_profile)

    def test_first_page_contains_five_records_group_list_2(self):
        """Проверка паджинатора для странцы с сортировкой по группе."""
        response = self.authorized_client_author.get(reverse('posts:group_posts', kwargs={
            'slug': PostVIEWSTests.group_1.slug}))
        self.assertEqual(len(response.context['page_obj']), 6)

    def test_first_page_contains_five_records_profile(self):
        """Проверка паджинатора для страницы профиля."""
        response = self.authorized_client_author.get(reverse('posts:profile', kwargs={
            'username': PostVIEWSTests.user.username}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_group_in_all_list(self):
        test_post = 1
        response_group = self.authorized_client_author.get(
            reverse('posts:group_posts', kwargs={
                'slug': PostVIEWSTests.group_2.slug
            }))
        response_profile = self.authorized_client_author.get(
            reverse('posts:profile', kwargs={
                'username': PostVIEWSTests.user.username
            }))
        self.context_test(test_post, response_group)
        self.context_test(test_post, response_profile)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImagePostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Первая группа',
            slug='test_slug',
            description='Тестовое описание первой группы',
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(ImagePostViewsTests.user)

    def test_image_in_post(self):
        """Проверка поста на наличие картинки на страницах."""
        templates_pages_names = {
            'posts/group_list.html': (
                reverse('posts:group_posts', kwargs={
                    'slug': ImagePostViewsTests.group.slug})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={
                    'username': ImagePostViewsTests.user.username})
            ),

        }
        post_image = ImagePostViewsTests.post
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_author.get(reverse_name)
                self.assertEqual(response.context['page_obj'][0].image, post_image.image)
        response_post_detail = self.authorized_client_author.get(
            reverse('posts:post_detail', kwargs={
                'post_id': ImagePostViewsTests.post.id
            }))
        self.assertEqual(response_post_detail.context['post'].image, post_image.image)


class CommentPostViewsTest(TestCase):
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
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(CommentPostViewsTest.user)

    def test_comments_in_post(self):
        """Проверка наличеи комментайрия на посте."""
        response = self.authorized_client.get(
            f'/posts/{CommentPostViewsTest.post.id}/')
        test_comment = response.context['comments'][0].text
        result_comment = CommentPostViewsTest.comment.text
        self.assertEqual(result_comment, test_comment)


class CacheIndexTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='Тестовый комментарий'
        )

    def setUp(self):
        self.guest_client = Client()

    def test_comments_in_post(self):
        """Проверка наличие комментайрия на посте."""
        response = self.guest_client.get(reverse('posts:index'))
        post1 = response.content
        Post.objects.all().delete()
        response = self.guest_client.get(reverse('posts:index'))
        post2 = response.content
        self.assertIn(post1, post2)
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        post3 = response.content
        self.assertNotIn(post2, post3)


class FollowUserTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='auth2')
        cls.user3 = User.objects.create_user(username='auth3')
        cls.post1 = Post.objects.create(
            author=cls.user2,
            text='Тестовый пост автора 2',
        )
        cls.post2 = Post.objects.create(
            author=cls.user3,
            text='Тестовый пост автора 3',
        )
        cls.follow = Follow.objects.create(
            user=cls.user1,
            author=cls.user2
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(FollowUserTests.user1)
        self.authorized_client_two = Client()
        self.authorized_client_two.force_login(FollowUserTests.user3)

    def test_follow_in_user(self):
        """Проверка работы подпсики на юзера."""
        count_followers = Follow.objects.count()
        self.authorized_client.get(
            (f'/profile/{FollowUserTests.user3.username}/follow/'))
        self.assertEqual(count_followers + 1, Follow.objects.count())

    def test_unfollow_in_user(self):
        """Проверка работы отписки от юзера."""
        count_followers = Follow.objects.count()
        self.authorized_client.get(
            f'/profile/{FollowUserTests.user2.username}/unfollow/'
        )
        self.assertEqual(count_followers - 1, Follow.objects.count())

    def test_new_post_in_follower_page(self):
        """Проверка работы появление постов от подписки."""
        response_one = self.authorized_client.get('/follow/')
        text_user2 = response_one.context['page_obj'][0].text
        self.assertEqual(text_user2, FollowUserTests.post1.text)
        response_two = self.authorized_client_two.get('/follow/')
        text_user3 = response_two.context['page_obj']
        self.assertNotEqual(text_user3, FollowUserTests.post2.text)
