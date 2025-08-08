from unittest.mock import patch
from tests.base import BaseTestCase
from models import db, User, Site
from werkzeug.security import generate_password_hash

class AppTestCase(BaseTestCase):
    def _login_user(self):
        # Helper function to register and log in a user
        self.client.post('/auth/register', data={
            'email': 'testuser@example.com',
            'password': 'password'
        }, follow_redirects=True)

        self.client.post('/auth/login', data={
            'email': 'testuser@example.com',
            'password': 'password'
        }, follow_redirects=True)

        with self.app.app_context():
            user = User.query.filter_by(email='testuser@example.com').first()
            return user.id

    def test_dashboard_loads_after_login(self):
        self._login_user()
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Your Sites', response.data)

    @patch('site_views.crawl_site')
    def test_add_site(self, mock_crawl_site):
        user_id = self._login_user()

        with self.app.app_context():
            response = self.client.post('/site/add', data={
                'name': 'Test Site',
                'url': 'http://example.com'
            }, follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Test Site', response.data)

            site = Site.query.filter_by(name='Test Site').first()
            self.assertIsNotNone(site)
            self.assertEqual(site.user_id, user_id)

            # Check that the crawler was called
            mock_crawl_site.assert_called_once_with(site.id, 'http://example.com')

    def test_site_access_control(self):
        user_id = self._login_user()

        with self.app.app_context():
            # Create a site for another user
            other_user_pw = generate_password_hash('otherpassword')
            other_user = User(email='other@user.com', password_hash=other_user_pw)
            db.session.add(other_user)
            db.session.commit()

            other_site = Site(name='Other Site', url='http://other.com', user_id=other_user.id)
            db.session.add(other_site)
            db.session.commit()
            other_site_id = other_site.id

        # Try to access the other user's site
        response = self.client.get(f'/site/{other_site_id}')
        self.assertEqual(response.status_code, 403)
