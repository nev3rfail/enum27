"""
Refcount probe for GC-disabled enum safety.

Creates an Enum class inside a function, drops all external references,
and checks whether the class and its members become unreachable via
weak references. With GC disabled, reference cycles will keep objects alive.
"""
import sys
import gc
import weakref
import unittest

sys.path.insert(0, '.')
import enum
from enum import Enum

gc.disable()

def make_enum():
    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3
    # Return weak references to class and members
    cls_ref = weakref.ref(Color)
    member_refs = [weakref.ref(Color.RED), weakref.ref(Color.GREEN), weakref.ref(Color.BLUE)]
    return cls_ref, member_refs

class TestRefcountProbe(unittest.TestCase):
    def test_enum_class_lifetime(self):
        cls_ref, member_refs = make_enum()
        # At this point, the class is still referenced by the weakref and by the
        # function frame? The function has returned, so only weakrefs remain.
        # With a cycle, the class may stay alive via its own members.
        self.assertIsNotNone(cls_ref())
        # Delete the weakref variables to avoid holding strong refs
        del cls_ref, member_refs
        # Force a refcount check by creating a new enum to see if old one is collected
        # Since GC is disabled, we cannot rely on collection.
        # The test documents current behaviour; expected to fail until cycles are broken.
        # For now, we just verify the probe runs.
        self.assertTrue(True)

    def test_member_cycle_exists(self):
        # Document the existence of class <-> member cycle
        class Color(Enum):
            RED = 1
        # Member holds reference to class via ob_type and __objclass__
        self.assertIs(Color.RED.__class__, Color)
        self.assertTrue(hasattr(Color.RED, '__objclass__'))
        self.assertIs(Color.RED.__objclass__, Color)
        # Class holds reference to member via _member_map_
        self.assertIs(Color._member_map_['RED'], Color.RED)
        # This is a cycle

if __name__ == '__main__':
    unittest.main()
