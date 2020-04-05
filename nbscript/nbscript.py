#!/usr/bin/env python3

import argparse
import contextlib
import json
import logging
import os
import re
import shlex
import subprocess
import sys
import time

import nbformat
import nbconvert

LOG = logging.getLogger('nbscript')
LOG.setLevel(logging.DEBUG)
if sys.version_info[0] >= 3:
    logging.lastResort.setLevel(logging.INFO)
else:
    ch = logging.lastResort = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    LOG.addHandler(ch)


if 'NB_ARGV' in os.environ:
    argv = json.loads(os.environ['NB_ARGV'])
else:
    argv = None

DEFAULT_FORMAT_STDOUT = 'asciidoc'
DEFAULT_FORMAT_FILE = 'ipynb'
# extension  -->  nbconvert --to format
EXT_MAP = {'ipynb': 'notebook', 'md': 'markdown', 'txt': 'asciidoc'}
# nbconvert --to format  -->  extension
FORMAT_MAP = {v: k for k, v in EXT_MAP.items()}


@contextlib.contextmanager
def setenv_context(key, value):
    """Set an environment variable as a context manager, restore it after"""
    old = os.environ.get(key)
    os.environ[key] = value
    yield
    if old is None:   del os.environ[key]
    else:             os.environ[key] = old

def nbscript(argv=sys.argv[1:], _return_names=False):
    if os.environ.get('NBSCRIPT_RUNNING') is not None:
        LOG.critical("Detected that we are already in snotebook... not executing again.")
        sys.exit(0)

    parser_outer = argparse.ArgumentParser(usage="nbscript [nbscript and nbconvert args] notebook [nb_argv ...]")
    parser_outer.add_argument("--to", help="Convert to this format (same as nbconvert --to option).")
    #parser_outer.add_argument("--export", "-e", action='append', help="Set environment variable (format NAME=VALUE)")
    parser_outer.add_argument("--output", "-o",
                              help="Filename to write to")
    parser_outer.add_argument("--save", action='store_true',
                              help="Save the notebook with an automatic filename")
    parser_outer.add_argument("--timestamp", "--ts", action='store_true',
                              help="Timestamp output filename (timestamp automatically "
                                   "added before extension)")
    parser_outer.add_argument("--verbose", "-v", action="store_true",
                              help="Verbose")
    parser_outer.add_argument("notebook",
                              help="Input notebook")
    parser_outer.add_argument("nb_argv", nargs=argparse.REMAINDER,
                              help="Output filename (basename, no extension)")

    # `nbconvert_args` is everything unknown *before* the `notebook`
    # argument, nb_argv is everything unknown after.
    args, nbconvert_args        = parser_outer.parse_known_args(argv)

    if args.verbose:
        logging.lastResort.setLevel(logging.DEBUG)
    LOG.debug('args: %s', args)
    LOG.debug("nbconvert_args: %s", nbconvert_args)
    sys.stdout.flush()


    os.environ['NB_NAME'] = args.notebook
    os.environ['NB_ARGV'] = json.dumps([args.notebook] + args.nb_argv)
    #if args.nbconvert_args:
    #    nbconvert_args = args.nbconvert_args.split()
    #else:
    #    nbconvert_args = [ ]

    # Manually do nbconvert process (not working yet)
    #nb = nbformat.read(open(args.notebook), as_version=4)
    #nbc, resc = preprocessor(nbc, resc)
    #nb = nbconvert.preprocessors.execute.executenb(nb, cwd=None)
    #self.writer.write(output, resources, notebook_name=notebook_name)

    #output_basename = args.notebook+'`date +%Y-%m-%d_%H:%M:%S`'
    to_format = args.to
    output_fname = args.output
    # determine to_format: first from the option, then from output filename,
    # then markdown by default.
    if to_format is None:
        #(infer from output)
        if output_fname:
            basename, ext = os.path.splitext(output_fname)
            if ext:
                ext = ext[1:]
            if ext not in EXT_MAP:
                raise RuntimeError("If saving to a file, you must give a known extension or use --to=FORMAT")
            to_format = EXT_MAP.get(ext)
        elif args.save:
            to_format = DEFAULT_FORMAT_FILE
        else:
            to_format = DEFAULT_FORMAT_STDOUT

    # --save inferrs a filename from the input filename
    if args.save:
        basename, oldext = os.path.splitext(args.notebook)
        if oldext:
            oldext = oldext[1:]
        ext = FORMAT_MAP.get(to_format, to_format)
        if ext == oldext:
            basename += '.out'
        output_fname = basename + '.' + ext

    # Make the saving arguments.  Stdout if a filename not given, otherwise to
    # the filename given.
    output_fname_before_timestamp = output_fname # pylint: disable=possibly-unused-variable
    if output_fname is None:
        output = ['--stdout', '--to', to_format]
    else:
        # output_filename is defined
        if args.timestamp:
            # adjust output filename
            basename, ext = os.path.splitext(output_fname)
            if args.timestamp:
                basename += time.strftime('.%Y-%m-%d_%H:%M:%S')
            output_fname = basename + ext
        if output_fname == args.notebook:
            raise ValueError("Input name is the same as the output name, so refusing to convert")
        # "--output-dir=." is added, because by default the dirname of the
        # input file gets unconditionally joined to the output path.  The other
        # alternative is abspath of the output filename.
        # see FilesWriter.build_directory in
        #   https://nbconvert.readthedocs.io/en/latest/config_options.html
        output = ['--output-dir=.', '--output', output_fname, '--to', to_format]

    if _return_names:
        return locals()

    # Do the conversion
    cmd_nbconvert = ['jupyter', 'nbconvert',
                    '--execute', '--allow-errors', '--ExecutePreprocessor.timeout=None',
                    ] + output + nbconvert_args + [
                    args.notebook,
                    ]
    LOG.debug('cmd_nbconvert: %s', cmd_nbconvert)
    LOG.debug('NB_ARGV: %s', os.environ.get('NB_ARGV'))
    sys.stdout.flush()

    with setenv_context('NBSCRIPT_RUNNING', 'True'):
        p = subprocess.Popen(cmd_nbconvert)
        p.wait()

    return(p.returncode)


if __name__ == "__main__":
    nbscript(argv=sys.argv[1:])
