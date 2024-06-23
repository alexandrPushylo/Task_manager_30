from unittest import TestCase, main
import doctest


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite('...'))
    return tests


class TestTemplate(TestCase):
    def test_template(self):
        self.assertTrue(True)


if __name__ == '__main__':
    main()
