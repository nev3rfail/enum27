"""
Isolation tests for enum34 behavior differences between Python 2 and Python 3.

These tests verify that the enum27 backport produces the same observable
behaviour as enum34 on the current interpreter, and explicitly document
points where Python 2 lacks __prepare__ support.
"""
import sys
import unittest

pyver = float('%s.%s' % sys.version_info[:2])

sys.path.insert(0, '.')
import enum
from enum import Enum, EnumMeta, _EnumDict

class TestPrepareAndDictType(unittest.TestCase):
    def test_enummeta_prepare_exists(self):
        self.assertTrue(hasattr(EnumMeta, '__prepare__'))

    def test_prepare_returns_enumdict_on_py3(self):
        if pyver >= 3.0:
            d = EnumMeta.__prepare__('X', (Enum,))
            self.assertIsInstance(d, _EnumDict)
        else:
            class X(Enum):
                A = 1
                B = 2
            self.assertIsInstance(X._member_map_, dict)
            self.assertEqual(X._member_names_, ['A', 'B'])

    def test_member_names_populated(self):
        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3
        self.assertEqual(Color._member_names_, ['RED', 'GREEN', 'BLUE'])
        self.assertEqual(list(Color), [Color.RED, Color.GREEN, Color.BLUE])

class TestOrderHandling(unittest.TestCase):
    def test_explicit_order_overrides_definition_order(self):
        class Season(Enum):
            _order_ = 'WINTER SUMMER SPRING AUTUMN'
            SPRING = 1
            SUMMER = 2
            AUTUMN = 3
            WINTER = 4
        self.assertEqual(Season._member_names_, ['WINTER', 'SUMMER', 'SPRING', 'AUTUMN'])
        self.assertEqual(list(Season), [Season.WINTER, Season.SUMMER, Season.SPRING, Season.AUTUMN])

    def test_order_string_parsing(self):
        class Ordered(Enum):
            __order__ = 'first second third'
            first = 'a'
            second = 'b'
            third = 'c'
        self.assertEqual(Ordered._member_names_, ['first', 'second', 'third'])

class TestMemberValidation(unittest.TestCase):
    def test_duplicate_name_raises_type_error(self):
        d = _EnumDict()
        d['A'] = 1
        with self.assertRaises(TypeError):
            d['A'] = 2

    def test_sunder_name_reserved(self):
        d = _EnumDict()
        with self.assertRaises(ValueError):
            d['_foo_'] = 1

    def test_descriptor_overwrites_member_raises(self):
        # _EnumDict raises TypeError when a name already in _member_names is reused
        d = _EnumDict()
        d['X'] = 1
        desc = property(lambda self: None)
        with self.assertRaises(TypeError):
            d['X'] = desc

class TestPython2Specifics(unittest.TestCase):
    def test_unicode_class_name_handling(self):
        # Verify Enum creation works with unicode names on Python 2
        if pyver < 3.0:
            class U(Enum):
                A = 1
            self.assertEqual(U.A.value, 1)

    def test_classdict_conversion_on_py2(self):
        if pyver < 3.0:
            class X(Enum):
                A = 1
                B = 2
            self.assertIn('A', X._member_map_)
            self.assertIn('B', X._member_map_)
            self.assertEqual(len(X), 2)

    def test_order_fallback_without_prepare(self):
        if pyver < 3.0:
            class Y(Enum):
                _order_ = 'B A'
                A = 1
                B = 2
            self.assertEqual(Y._member_names_, ['B', 'A'])

if __name__ == '__main__':
    unittest.main()
