import unittest
from unittest.mock import patch, MagicMock
from main import app

class TestHoraryAPI(unittest.TestCase):
    @patch('astro_core.Nominatim')
    @patch('astro_core.swe')
    def test_horary_chart_endpoint(self, mock_swe, mock_nominatim):
        from fastapi.testclient import TestClient
        client = TestClient(app)
        mock_geo = MagicMock()
        mock_geo.latitude = 55.75
        mock_geo.longitude = 37.62
        mock_nominatim.return_value.geocode.return_value = mock_geo
        mock_swe.julday.return_value = 2450000.5
        def fake_calc_ut(jd, code):
            idx = int(code) % 10
            return [[idx*36.0, 0, 0, -1.0 if idx % 2 == 0 else 1.0]]
        mock_swe.calc_ut.side_effect = fake_calc_ut
        mock_swe.houses.return_value = ([10.0]*12, None)
        resp = client.get("/horary_chart", params={
            "date": "2025-06-13", "time": "15:00", "place": "Moscow", "tz_offset": 3
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["type"], "horary")
        self.assertIn("question_time", data)
        self.assertIn("place", data)
        self.assertIn("chart", data)
        self.assertIn("planet_degrees", data["chart"])
        self.assertIn("houses", data["chart"])
        self.assertIn("aspects", data["chart"])

if __name__ == '__main__':
    unittest.main()
