import unittest

from app import User, app, db
from find_city import get_coords_by_name


class TestGetCoordsByName(unittest.TestCase):
    def test_existing_city(self):
        name_city = "Москва"
        expected_lat = 55.755833333333
        expected_lon = 37.617777777778

        lat, lon = get_coords_by_name(name_city)

        self.assertAlmostEqual(float(lat), expected_lat, places=4)
        self.assertAlmostEqual(float(lon), expected_lon, places=4)

    def test_non_existing_city(self):
        name_city = "Несуществующий город"
        lat, lon = get_coords_by_name(name_city)

        self.assertIsNone(lat)
        self.assertIsNone(lon)


class FlaskAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SECRET_KEY"] = "test_secret_key"
        cls.app = app
        cls.client = app.test_client()

    @classmethod
    def setUp(cls):
        with cls.app.app_context():
            db.create_all()

    @classmethod
    def tearDown(cls):
        with cls.app.app_context():
            db.drop_all()

    def test_register(self):
        response = self.client.post(
            "/register",
            data={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123",
            },
        )
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            user = User.query.filter_by(username="testuser").first()
            self.assertIsNotNone(user)
            self.assertEqual(user.email, "test@example.com")
            self.assertTrue(user.check_password("password123"))

    def test_register_existing_user(self):
        self.client.post(
            "/register",
            data={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123",
            },
        )

        response = self.client.post(
            "/register",
            data={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Пользователь с таким именем или email уже существует",
            response.data.decode("utf-8"),
        )

    def test_login(self):
        self.client.post(
            "/register",
            data={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123",
            },
        )

        response = self.client.post(
            "/login", data={"username": "testuser", "password": "password123"}
        )
        self.assertEqual(response.status_code, 302)

    def test_login_invalid_user(self):
        response = self.client.post(
            "/login", data={"username": "invaliduser", "password": "wrongpassword"}
        )
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.client.post(
            "/register",
            data={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123",
            },
        )
        self.client.post(
            "/login", data={"username": "testuser", "password": "password123"}
        )

        response = self.client.get("/logout")
        self.assertEqual(response.status_code, 302)

    def test_main_weather(self):
        self.client.post(
            "/register",
            data={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123",
            },
        )
        self.client.post(
            "/login", data={"username": "testuser", "password": "password123"}
        )

        response = self.client.get("/main_weather")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
