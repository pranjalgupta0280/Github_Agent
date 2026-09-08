import unittest
from calculator import add, divide

class TestCalculator(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

    def test_divide_valid(self):
        self.assertEqual(divide(10, 2), 5)

    def test_divide_by_zero(self):
        # Issue: divide(10, 0) should safely return None or 0, but currently raises ZeroDivisionError
        self.assertIsNone(divide(10, 0))

if __name__ == '__main__':
    unittest.main()
