from tests.base import BaseTestCase
from models import db, User
from werkzeug.security import check_password_hash

class AuthTestCase(BaseTestCase):
    def test_register_page_loads(self):
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create Your Account', response.data)

    def test_user_registration(self):
        with self.app.app_context():
            # Register a new user
            response = self.client.post('/auth/register', data={
                'email': 'test@example.com',
                'password': 'password123'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Registration successful', response.data)

            # Check if the user is in the database
            user = User.query.filter_by(email='test@example.com').first()
            self.assertIsNotNone(user)
            self.assertTrue(check_password_hash(user.password_hash, 'password123'))

    def test_login_and_logout(self):
        # First, register a user to log in with
        self.client.post('/auth/register', data={
            'email': 'loginuser@example.com',
            'password': 'password'
        })

        # Test login
        response = self.client.post('/auth/login', data={
            'email': 'loginuser@example.com',
            'password': 'password'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to the SEO Topic Cluster Tool', response.data)

        # Check that we are logged in by accessing dashboard
        dashboard_response = self.client.get('/dashboard', follow_redirects=True)
        self.assertIn(b'Add a New Site', dashboard_response.data)

        # Test logout
        logout_response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(logout_response.status_code, 200)
        self.assertIn(b'Log In', logout_response.data)

        # Check that we are logged out
        dashboard_response_after_logout = self.client.get('/dashboard', follow_redirects=True)
        self.assertIn(b'Log In to Your Account', dashboard_response_after_logout.data)
