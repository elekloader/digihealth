# SPDX-License-Identifier: GPL-2.0-or-later
"""An optional write policy: a Python file installed on one computer that the
runner asks before it changes anything on a unit, for example to keep
automated test sessions away from the person's own projects. Without one, the
runner writes wherever it is told and gives an item exactly the name it was
asked for.

What the policy covers, and what it does not. It is asked before the runner
sends dumps (`send`), saves a project (`save-project`) and renames. It is not
asked before the key steps (`tap`, `hold`, `release`, `keys`, `turn`): those
press the unit's own buttons, and anything the panel can do, including saving
over or deleting a project, they can do. A policy is a guard against mistakes
in a test plan's data steps, not a sandbox for a plan's key steps. The runner
does check where a `save-project` landed (see digirun.py).

The runner executes the policy file: it is Python from this computer's config
folder (or the file ANALOGHEALTH_POLICY names), so treat that folder like any
other place code runs from.

The policy is the file named by ANALOGHEALTH_POLICY (empty: none), else
policy.py in the analoghealth config folder (%LOCALAPPDATA%\\analoghealth on
Windows, ~/.config/analoghealth elsewhere). It may define any of these; a hook
refuses by raising writepolicy.Refused:

    check_write(rpc, path, new_name)   before a write, clear or rename of path:
                                       -> the name the item carries afterwards,
                                       or None to leave it as written
    before_dumps(session, msgs)        before SysEx messages go to the unit
    before_save_project(session, path)  before the keys of a key-driven project save
                                       into a slot that holds a project, e.g. to
                                       empty it (the save itself needs an empty slot)
    after_save_project(session, path, name)   after a key-driven project save
    before_save_kit(session)           before a key-driven kit save
    describe_active(kit_name)          a short note for `analogrun active`

The last three may return a line for the runner to print. unitdata.py has the
data-store and dump helpers a policy needs.

This is the same loader, hooks and policy file as analoghealth's writepolicy.py,
so one policy serves the Analog Rytm / Four runner and digirun.py alike. A
digirun session has `unit = 'digitone'`, so a policy can tell the two apart
(the Digitone keeps its project's name in pattern dumps: unitdata.pattern_name).
"""
import importlib.util
import os
import sys

_loaded = {}


class Refused(Exception):
    """A write the local policy does not allow."""


def config_dir():
    base = os.environ.get('LOCALAPPDATA') if sys.platform == 'win32' else None
    return os.path.join(base or os.path.join(os.path.expanduser('~'), '.config'), 'analoghealth')


def policy_path():
    """-> the policy file to use, or None."""
    if 'ANALOGHEALTH_POLICY' in os.environ:
        return os.environ['ANALOGHEALTH_POLICY'] or None
    return os.path.join(config_dir(), 'policy.py')


def policy():
    """The loaded policy module, or None when there is no policy file."""
    path = policy_path()
    if not path or not os.path.isfile(path):
        return None
    if path not in _loaded:
        spec = importlib.util.spec_from_file_location('analoghealth_policy', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _loaded[path] = mod
    return _loaded[path]


def _hook(name):
    return getattr(policy(), name, None)


def installed():
    return policy() is not None


def check_write(rpc, path, new_name=None):
    hook = _hook('check_write')
    if hook:
        return hook(rpc, path, new_name)
    return new_name or None


def before_dumps(session, msgs):
    hook = _hook('before_dumps')
    return hook(session, msgs) if hook else None


def before_save_project(session, path):
    hook = _hook('before_save_project')
    return hook(session, path) if hook else None


def after_save_project(session, path, name):
    hook = _hook('after_save_project')
    return hook(session, path, name) if hook else None


def before_save_kit(session):
    hook = _hook('before_save_kit')
    return hook(session) if hook else None


def describe_active(kit_name):
    hook = _hook('describe_active')
    return hook(kit_name) if hook else None
