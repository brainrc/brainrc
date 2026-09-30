import contextlib
import io
import unittest

from greet import greet, main


class GreetTest(unittest.TestCase):
    def test_greet(self):
        self.assertEqual(greet("Ada"), "Hello, Ada!")

    def test_main_default_name(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main([]), 0)
        self.assertEqual(out.getvalue(), "Hello, world!\n")


if __name__ == "__main__":
    unittest.main()
