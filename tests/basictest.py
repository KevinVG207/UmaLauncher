import unittest
import sys
sys.path.append("../umalauncher")
import os
os.chdir("../umalauncher")

class TestTest(unittest.TestCase):

    def test_test(self):
        self.assertEqual(1, 1)


if __name__ == '__main__':
    unittest.main()