import unittest
from unittest.mock import patch, MagicMock
from main import app

class TestTransitAPI(unittest.TestCase):
    @patch('astro_core.Nominatim')
    @patch('astro_core.swe')
    def test_transits_endpoint(self, mock_swe, mock_nominatim):
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
        resp = client.get("/transits", params={
            "natal_date": "2000-01-01", "natal_time": "12:00", "natal_place": "Moscow", "natal_tz_offset": 3,
            "transit_date": "2025-06-13", "transit_time": "15:00"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("natal", data)
        self.assertIn("transit", data)
        self.assertIn("aspects", data)
        self.assertIn("planet_degrees", data["natal"])
        self.assertIn("planet_degrees", data["transit"])
        self.assertIsInstance(data["aspects"], list)

if __name__ == '__main__':
    unittest.main()
