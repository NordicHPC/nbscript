# This is a file
# pylint: disable=unused-argument,redefined-outer-name

import contextlib
import glob
import logging
import os
from os.path import join, dirname
import shutil
import tempfile
import time

import pytest

from nbscript.nbscript import nbscript, LOG as nbscript_LOG
nbscript_LOG.setLevel(logging.DEBUG)


@contextlib.contextmanager
def chdir_context(name):
    old = os.getcwd()
    os.chdir(name)
    yield
    os.chdir(old)

@pytest.fixture
def tdir():
    tmpdir = tempfile.mkdtemp(prefix='nbscript-test')
    shutil.copy(join(dirname(__file__), 'testdata', 'one.ipynb'), tmpdir)
    with chdir_context(tmpdir):
        yield tmpdir
    shutil.rmtree(tmpdir)

def assert_out(fname):
    if not os.path.exists(fname):
        print('directory contains:', os.listdir(dirname(fname) or '.'))
    assert os.path.exists(fname)
    assert '0123456789' in open(fname).read()

def test_basic_stdout(tdir, capfd):
    """Test notebook run on stdout"""
    nbscript(['one.ipynb'])
    captured = capfd.readouterr()
    assert '0123456789' in captured.out

def test_basic_save(tdir):
    """Test notebook run on stdout"""
    nbscript(['-o', 'out.md', 'one.ipynb'])
    assert_out('out.md')

@pytest.mark.parametrize("fmt,output",
                         [('',           'one.md'),
                          ('markdown',   'one.md'),
                          #('asciidoc',   'one.txt'),   # adds .asciidoc as file name extension
                          ('notebook',   'one.nbscript.ipynb'),
                         ])
def test_save(tdir, fmt, output):
    to = ['--to', fmt] if fmt else []
    nbscript(to + ['--save', 'one.ipynb'])
    assert_out(output)

def test_timestamp_save(tdir):
    nbscript(['--save', '--timestamp', 'one.ipynb'])
    print(os.listdir('.'))
    output = glob.glob('*.md')[0]
    assert time.strftime('%Y-%m-%d') in output

def test_timestamp_filename(tdir):
    nbscript(['--out', 'out.ipynb', '--timestamp', 'one.ipynb'])
    output = glob.glob('out*')[0]
    assert time.strftime('%Y-%m-%d') in output

def test_detect_not_running(tdir):
    import nbscript
    assert not nbscript.argv, "Running detected but we shouldn't be"

def test_detect_running(tdir, capfd):
    nbscript(['one.ipynb'])
    captured = capfd.readouterr()
    assert 'Yes running nbscript' in captured.out


@pytest.mark.parametrize("argv",
                         [('A', 'B'),
                          ('A', '--B'),
                          ('--A', 'B'),
                          ('--A', '--B'),
                         ])
def test_argv(tdir, capfd, argv):
    nbscript(['one.ipynb'] + list(argv))
    captured = capfd.readouterr()
    assert " ".join(argv) in captured.out
