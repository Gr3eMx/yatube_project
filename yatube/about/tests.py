from http import HTTPStatus


def test_urls_uses_correct_template(self):
    """Страницы доступна любому пользователю."""
    templates_url_names = {
        '/about/author/': 'about/author.html',
        '/about/tech/': 'about/tech.html',

    }
    for address, template in templates_url_names.items():
        with self.subTest(address=address):
            response = self.guest_client.get(address)
            self.assertEqual(response.status_code, HTTPStatus.OK)