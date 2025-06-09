import unittest
from unittest.mock import patch, MagicMock
from main import calculate_chart, get_week_transits

class TestAstroAPI(unittest.TestCase):
    @patch('main.Nominatim')
    @patch('main.swe')
    def test_calculate_chart_valid(self, mock_swe, mock_nominatim):
        # Mock geocode
        mock_geo = MagicMock()
        mock_geo.latitude = 55.75
        mock_geo.longitude = 37.62
        mock_nominatim.return_value.geocode.return_value = mock_geo
        # Mock swe
        mock_swe.julday.return_value = 2450000.5
        mock_swe.calc_ut.return_value = ([123.45],)
        mock_swe.houses.return_value = ([10.0]*12, None)
        # Call
        data, err = calculate_chart('2000-01-01', '12:00', 'Moscow', 3)
        self.assertIsNone(err)
        self.assertIn('planet_degrees', data)
        self.assertEqual(len(data['planet_degrees']), 10)
        self.assertEqual(len(data['houses']), 12)

    @patch('main.Nominatim')
    def test_calculate_chart_invalid_place(self, mock_nominatim):
        mock_nominatim.return_value.geocode.return_value = None
        data, err = calculate_chart('2000-01-01', '12:00', 'Nowhere', 3)
        self.assertIsNone(data)
        self.assertIsNotNone(err)
        self.assertEqual(err.status_code, 400)

    @patch('main.swe')
    def test_get_week_transits(self, mock_swe):
        # Setup natal chart
        natal = {
            'planet_degrees': {n: i*30.0 for i, n in enumerate([
                'Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
                'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'])},
            'houses': [i*30.0 for i in range(12)]
        }
        # Mock swe
        mock_swe.calc_ut.return_value = ([45.0],)
        # Call
        week = get_week_transits(natal, 2450000.5, days=3)
        self.assertEqual(len(week), 3)
        for day in week:
            self.assertIn('transits', day)
            self.assertIn('aspects', day)
            self.assertIn('houses', day)

    @patch('main.Nominatim')
    @patch('main.swe')
    @patch('main.draw_chart')
    def test_natal_chart_image(self, mock_draw_chart, mock_swe, mock_nominatim):
        # Mock geocode
        mock_geo = MagicMock()
        mock_geo.latitude = 55.75
        mock_geo.longitude = 37.62
        mock_nominatim.return_value.geocode.return_value = mock_geo
        # Mock swe
        mock_swe.julday.return_value = 2450000.5
        mock_swe.calc_ut.return_value = ([123.45],)
        mock_swe.houses.return_value = ([10.0]*12, None)
        # Mock draw_chart
        mock_draw_chart.return_value = b'binaryimage'

        from main import natal_chart_image
        class DummyQuery:
            def __init__(self, val): self.val = val
            def __call__(self, *a, **k): return self.val
        # Call endpoint
        resp = natal_chart_image(
            date='2000-01-01',
            time='12:00',
            place='Moscow',
            tz_offset=3
        )
        self.assertTrue(hasattr(resp, 'media_type'))
        self.assertEqual(resp.media_type, 'image/png')
        self.assertEqual(resp.body, b'binaryimage')

    @patch('main.Nominatim')
    @patch('main.swe')
    def test_draw_chart_produces_image_file(self, mock_swe, mock_nominatim):
        # Mock geocode
        mock_geo = MagicMock()
        mock_geo.latitude = 55.75
        mock_geo.longitude = 37.62
        mock_nominatim.return_value.geocode.return_value = mock_geo
        # Mock swe
        mock_swe.julday.return_value = 2450000.5
        mock_swe.calc_ut.return_value = ([123.45],)
        mock_swe.houses.return_value = ([i*30.0 for i in range(12)], None)
        # Prepare chart data
        data, err = calculate_chart('2000-01-01', '12:00', 'Moscow', 3)
        from main import draw_chart
        img_bytes = draw_chart(data['planet_degrees'], data['houses'], [])
        # Write to file
        with open('test_chart.png', 'wb') as f:
            f.write(img_bytes)
        # Check file exists and is not empty
        import os
        self.assertTrue(os.path.exists('test_chart.png'))
        self.assertGreater(os.path.getsize('test_chart.png'), 0)
        # Additional check: verify house cusp values are present in the data
        self.assertEqual(len(data['houses']), 12)
        for i, cusp in enumerate(data['houses']):
            self.assertIsInstance(cusp, float)
        # Clean up
        os.remove('test_chart.png')

if __name__ == '__main__':
    unittest.main()
