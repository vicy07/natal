import unittest
from unittest.mock import patch, MagicMock
from logic_forecast import get_week_transits

class TestForecastAPI(unittest.TestCase):
    @patch('astro_core.swe')
    def test_get_week_transits(self, mock_swe):
        natal = {
            'planet_degrees': {n: i*30.0 for i, n in enumerate([
                'Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
                'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'])},
            'houses': [i*30.0 for i in range(12)]
        }
        mock_swe.calc_ut.return_value = ([45.0],)
        week = get_week_transits(natal, 2450000.5, days=3)
        self.assertEqual(len(week), 3)
        for day in week:
            self.assertIn('transits', day)
            self.assertIn('aspects', day)
            self.assertIn('houses', day)

if __name__ == '__main__':
    unittest.main()
