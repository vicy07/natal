import unittest
from unittest.mock import patch, MagicMock
from astro_core import calculate_chart
from chart_draw import draw_chart
from main import app

class TestNatalAPI(unittest.TestCase):
    @patch('astro_core.Nominatim')
    @patch('astro_core.swe')
    def test_calculate_chart_valid(self, mock_swe, mock_nominatim):
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
        data, err = calculate_chart('2000-01-01', '12:00', 'Moscow', 3)
        self.assertIsNone(err)
        self.assertIn('planet_degrees', data)
        self.assertEqual(len(data['planet_degrees']), 10)
        self.assertEqual(len(data['houses']), 12)
        self.assertIn('retrograde_planets', data)
        self.assertIn('aspects', data)

    @patch('astro_core.Nominatim')
    def test_calculate_chart_invalid_place(self, mock_nominatim):
        mock_nominatim.return_value.geocode.return_value = None
        data, err = calculate_chart('2000-01-01', '12:00', 'Nowhere', 3)
        self.assertIsNone(data)
        self.assertIsNotNone(err)
        self.assertIn("error", err)

    @patch('astro_core.Nominatim')
    @patch('astro_core.swe')
    @patch('logic_natal.draw_chart')
    def test_natal_chart_image(self, mock_draw_chart, mock_swe, mock_nominatim):
        mock_geo = MagicMock()
        mock_geo.latitude = 55.75
        mock_geo.longitude = 37.62
        mock_nominatim.return_value.geocode.return_value = mock_geo
        mock_swe.julday.return_value = 2450000.5
        mock_swe.calc_ut.return_value = ([123.45, 0, 0, 1.0],)
        mock_swe.houses.return_value = ([10.0]*12, None)
        mock_draw_chart.return_value = b'binaryimage'
        from logic_natal import natal_chart_image
        resp = natal_chart_image(
            date='2000-01-01',
            time='12:00',
            place='Moscow',
            tz_offset=3
        )
        self.assertTrue(hasattr(resp, 'media_type'))
        self.assertEqual(resp.media_type, 'image/png')
        self.assertEqual(resp.body, b'binaryimage')

    @patch('astro_core.Nominatim')
    @patch('astro_core.swe')
    def test_draw_chart_produces_image_file(self, mock_swe, mock_nominatim):
        mock_geo = MagicMock()
        mock_geo.latitude = 55.75
        mock_geo.longitude = 37.62
        mock_nominatim.return_value.geocode.return_value = mock_geo
        mock_swe.julday.return_value = 2450000.5
        def fake_calc_ut(jd, code):
            idx = int(code) % 10
            return [[idx*36.0, 0, 0, -1.0 if idx % 2 == 0 else 1.0]]
        mock_swe.calc_ut.side_effect = fake_calc_ut
        mock_swe.houses.return_value = ([i*30.0 for i in range(12)], None)
        from astro_core import calculate_chart
        from chart_draw import draw_chart
        data, err = calculate_chart('2000-01-01', '12:00', 'Moscow', 3)
        img_bytes = draw_chart(data['planet_degrees'], data['houses'], data['aspects'], data['retrograde_planets'])
        with open('test_chart.png', 'wb') as f:
            f.write(img_bytes)
        import os
        self.assertTrue(os.path.exists('test_chart.png'))
        self.assertGreater(os.path.getsize('test_chart.png'), 0)
        self.assertEqual(len(data['houses']), 12)
        for i, cusp in enumerate(data['houses']):
            self.assertIsInstance(cusp, float)
        self.assertTrue('Sun' in data['retrograde_planets'] or 'Moon' in data['retrograde_planets'])
        #os.remove('test_chart.png')

if __name__ == '__main__':
    unittest.main()
