import contextlib
import os
from os.path import join, dirname
import shutil
import tempfile

import pytest


@contextlib.contextmanager
def chdir_context(name):
    """chdir as a context manager"""
    old = os.getcwd()
    os.chdir(name)
    yield
    os.chdir(old)

def _tdir(ipynb_file='one.ipynb'):
    """Create temporary directory for test, copying in a test notebook"""
    tmpdir = tempfile.mkdtemp(prefix='nbscript-test')
    shutil.copy(join(dirname(__file__), 'testdata', ipynb_file), tmpdir)
    with chdir_context(tmpdir):
        yield tmpdir
    shutil.rmtree(tmpdir)

@pytest.fixture
def tdir():
    """Temporary testing dir, using one.ipynb"""
    for x in _tdir('one.ipynb'):
        yield x

@pytest.fixture
def tdir_slurm():
    """Temporary testing dir, using slurm.ipynb"""
    for x in _tdir('slurm.ipynb'):
        yield x

def assert_out(fname):
    """Assert a certain filename is written and contains the marker for successful integration"""
    if not os.path.exists(fname):
        print('directory contains:', os.listdir(dirname(fname) or '.'))
    assert os.path.exists(fname)
    assert '0123456789' in open(fname).read()


def assert_sublist(list_, sublist):
    n = len(sublist)
    for i in range(len(list_)-n):
        if list_[i:i+n] == sublist:
            return True
    raise AssertionError("Sublist: %s does not contain %s"%(list_, sublist))
