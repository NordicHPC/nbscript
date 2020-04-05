# pylint: disable=unused-argument,redefined-outer-name

import glob
import logging
import os
from os.path import join, dirname
import time

import pytest

from .nbscript import nbscript, LOG as nbscript_LOG
nbscript_LOG.setLevel(logging.DEBUG)
from .testutil import assert_out, chdir_context, tdir

def test_basic_stdout(tdir, capfd):
    """Test notebook run on stdout"""
    nbscript(['one.ipynb'])
    captured = capfd.readouterr()
    assert '0123456789' in captured.out

def test_basic_save(tdir):
    """Test notebook run on stdout"""
    nbscript(['-o', 'out.md', 'one.ipynb'])
    assert_out('out.md')

test_formats = [('', 'one.out.ipynb'),
                ('markdown',   'one.md'),
                #('asciidoc',   'one.txt'),   # adds .asciidoc as file name extension
                ('notebook',   'one.out.ipynb'),
                ]
@pytest.mark.parametrize("fmt,output", test_formats)
def test_save(tdir, fmt, output):
    to = ['--to', fmt] if fmt else []
    nbscript(to + ['--save', 'one.ipynb'])
    assert_out(output)

@pytest.mark.parametrize("fmt,output", test_formats)
def test_save_subdir(tdir, fmt, output):
    """Test when input is ../subdir/X.ipynb"""
    os.mkdir('subdir')
    os.rename('one.ipynb', 'subdir/one.ipynb')
    to = ['--to', fmt] if fmt else []
    nbscript(to + ['--save', 'subdir/one.ipynb'])
    assert_out('subdir/'+output)

@pytest.mark.parametrize("fmt,output", test_formats)
def test_save_parentdir(tdir, fmt, output):
    """Test when input is ../parentdir/X.ipynb"""
    os.mkdir('subdir')
    os.mkdir('parentdir')
    os.rename('one.ipynb', 'parentdir/one.ipynb')
    with chdir_context('subdir'):
        to = ['--to', fmt] if fmt else []
        nbscript(to + ['--save', '../parentdir/one.ipynb'])
    assert_out('parentdir/'+output)

@pytest.mark.parametrize("fmt,output", test_formats)
def test_save_abspath(tdir, fmt, output):
    """Test when input is abspath(../parentdir/X.ipynb)"""
    os.mkdir('subdir')
    os.mkdir('parentdir')
    os.rename('one.ipynb', 'parentdir/one.ipynb')
    with chdir_context('subdir'):
        to = ['--to', fmt] if fmt else []
        nbscript(to + ['--save', os.path.abspath('../parentdir/one.ipynb')])
    assert_out('parentdir/'+output)

def test_timestamp_save(tdir):
    nbscript(['--save', '--timestamp', 'one.ipynb'])
    print(os.listdir('.'))
    output = glob.glob('*.out.*.ipynb')[0]
    assert time.strftime('%Y-%m-%d') in output

def test_timestamp_save_subdir(tdir):
    """Test when input is subbir/X.ipynb"""
    os.mkdir('subdir')
    os.rename('one.ipynb', 'subdir/one.ipynb')
    nbscript(['--save', '--timestamp', 'subdir/one.ipynb'])
    print(os.listdir('subdir'))
    output = glob.glob('subdir/*.out.*.ipynb')[0]
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
