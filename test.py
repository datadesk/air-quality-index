import unittest

from air_quality_index import get_air_quality


class AirQualityIndexUnitTest(unittest.TestCase):
    def test_air_quality(self):
        get_air_quality()


if __name__ == "__main__":
    unittest.main()
