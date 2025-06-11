import unittest
from fastapi.testclient import TestClient
from main import app

class TestSynastryAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_synastry_basic(self):
        # Use two different dates/places for basic synastry
        response = self.client.get("/synastry", params={
            "date1": "1990-01-01", "time1": "12:00", "place1": "Moscow", "tz_offset1": 3,
            "date2": "1992-02-02", "time2": "15:00", "place2": "London", "tz_offset2": 0
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("person1", data)
        self.assertIn("person2", data)
        self.assertIn("synastry_aspects", data)
        self.assertIn("summary", data)
        self.assertIsInstance(data["synastry_aspects"], list)
        self.assertIsInstance(data["summary"], dict)

    def test_synastry_analytics(self):
        response = self.client.get("/synastry/analytics", params={
            "date1": "1990-01-01", "time1": "12:00", "place1": "Moscow", "tz_offset1": 3,
            "date2": "1992-02-02", "time2": "15:00", "place2": "London", "tz_offset2": 0
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("aspect_matrix", data)
        self.assertIn("personal_aspects", data)
        self.assertIn("most_exact_aspect", data)
        self.assertIn("aspect_type_count", data)
        self.assertIn("harmonious_details", data)
        self.assertIn("tense_details", data)
        self.assertIn("total_aspects", data)
        self.assertIsInstance(data["aspect_matrix"], dict)
        self.assertIsInstance(data["personal_aspects"], list)
        self.assertIsInstance(data["harmonious_details"], list)
        self.assertIsInstance(data["tense_details"], list)

if __name__ == "__main__":
    unittest.main()
