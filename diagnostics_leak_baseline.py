"""
Diagnostic baseline for GC-disabled enum leaks.

Creates a set of enum classes, records weak references, drops strong
references, and records which objects remain alive. Output is written to
diagnostics_baseline.json for later comparison after fixes.
"""
import sys
import gc
import weakref
import json
import os

sys.path.insert(0, '.')
import enum
from enum import Enum, IntEnum

gc.disable()

def make_enums():
    # Simple enum
    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    # IntEnum
    class Priority(IntEnum):
        LOW = 1
        MEDIUM = 2
        HIGH = 3

    # Enum with alias
    class Shape(Enum):
        CIRCLE = 1
        SQUARE = 1
        TRIANGLE = 2

    # Enum with explicit order
    class Season(Enum):
        _order_ = 'WINTER SPRING SUMMER AUTUMN'
        WINTER = 4
        SPRING = 1
        SUMMER = 2
        AUTUMN = 3

    # Functional API
    Planet = Enum('Planet', 'MERCURY VENUS EARTH MARS')

    return {
        'Color': Color,
        'Priority': Priority,
        'Shape': Shape,
        'Season': Season,
        'Planet': Planet,
    }

def capture_state(enums):
    data = {}
    for name, cls in enums.items():
        cls_ref = weakref.ref(cls)
        member_refs = {}
        for member_name in cls._member_names_:
            member = cls._member_map_[member_name]
            member_refs[member_name] = weakref.ref(member)
        data[name] = {
            'class_alive_before': cls_ref() is not None,
            'member_alive_before': {k: v() is not None for k, v in member_refs.items()},
            'member_count': len(cls._member_names_),
            'member_map_size': len(cls._member_map_),
        }
        # Store refs for later check
        data[name]['_cls_ref'] = cls_ref
        data[name]['_member_refs'] = member_refs
    return data

def drop_and_check(data):
    # Remove strong references to classes by deleting the dict
    # The data dict still holds weakrefs only
    results = {}
    for name, info in data.items():
        cls_ref = info['_cls_ref']
        member_refs = info['_member_refs']
        results[name] = {
            'class_alive_after': cls_ref() is not None,
            'member_alive_after': {k: v() is not None for k, v in member_refs.items()},
        }
    return results

def main():
    enums = make_enums()
    # Capture before drop
    state_before = capture_state(enums)
    # Drop strong refs to enums dict
    del enums
    # Force a small amount of work to ensure refs are released
    # With GC disabled, cycles will keep objects alive
    state_after = drop_and_check(state_before)

    # Build serializable output
    output = {}
    for name in state_before:
        output[name] = {
            'member_count': state_before[name]['member_count'],
            'member_map_size': state_before[name]['member_map_size'],
            'class_alive_before': state_before[name]['class_alive_before'],
            'class_alive_after': state_after[name]['class_alive_after'],
            'member_alive_before': state_before[name]['member_alive_before'],
            'member_alive_after': state_after[name]['member_alive_after'],
        }

    # Also record process-wide object counts
    try:
        obj_count = len(gc.get_objects())
    except Exception:
        obj_count = None

    output['_meta'] = {
        'gc_enabled': gc.isenabled(),
        'python': sys.version,
        'obj_count': obj_count,
    }

    out_path = os.path.join(os.path.dirname(__file__), 'diagnostics_baseline.json')
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2, sort_keys=True)

    print('Baseline written to', out_path)
    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()
