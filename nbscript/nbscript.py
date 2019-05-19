#!/usr/bin/env python3

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time

import nbformat
import nbconvert

if 'NB_ARGV' in os.environ:
    argv = json.loads(os.environ['NB_ARGV'])
else:
    argv = None


def nbscript(argv=sys.argv[1:]):
    if os.environ.get('NBSCRIPT_RUNNING') is not None:
        print("Detected that we are already in snotebook... not executing again.")
        exit(0)

    parser_outer = argparse.ArgumentParser(usage="nbscript [nbscript and nbconvert args] notebook [nb_argv ...]")
    parser_outer.add_argument("--to", help="Convert to this format (same as nbconvert --to option).")
    #parser_outer.add_argument("--export", "-e", action='append', help="Set environment variable (format NAME=VALUE)")
    parser_outer.add_argument("--output", "-o", help="Filename to write to")
    parser_outer.add_argument("--timestamp", "--ts", action='store_true',
                              help="Timestamp output filename (timestamp automatically "
                                   "added before extension)")
    parser_outer.add_argument("--verbose", "-v", action="store_true",
                              help="Verbose")
    parser_outer.add_argument("notebook", help="Input notebook")
    parser_outer.add_argument("nb_argv", nargs=argparse.REMAINDER, help="Output filename (basename, no extension)")

    # `nbconvert_args` is everything unknown *before* the `notebook`
    # argument, nb_argv is everything unknown after.
    args, nbconvert_args        = parser_outer.parse_known_args(argv)
    print(args)
    print("nbconvert_args:", nbconvert_args)
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
    if args.output:
        output_fname = args.output
        if to_format is None:
            basename, ext = os.path.splitext(args.notebook)
            if ext:
                ext = ext[1:]
            ext_map = {'ipynb': 'notebook', 'md': 'markdown', 'txt': 'asciidoc'}
            to_format = ext_map.get(ext, ext)
        if args.timestamp:
            basename += time.strftime('.%Y-%m-%d_%H:%M:%S')
        output_fname = basename + '.' + os.path.ext
        output = ['--output', output_fname, '--to', to_format]
        if output_fname == args.notebook:
            raise ValueError("Input name is the same as the output name, so refusing to convert")
    elif to_format:
        output = ['--stdout', '--to', to_format]
    # No output filename given: to stdout
    else:
        output = ['--stdout', '--to', 'markdown']

    os.environ['NBSCRIPT_RUNNING'] = 'True'
    cmd_nbconvert = ['jupyter', 'nbconvert',
                    '--execute', '--allow-errors', '--ExecutePreprocessor.timeout=None',
                    *output, *nbconvert_args,
                    args.notebook,
                    ]
    print(cmd_nbconvert)
    print('NB_ARGV:', os.environ.get('NB_ARGV'))
    sys.stdout.flush()

    p = subprocess.Popen(cmd_nbconvert)
    p.wait()

    return(p.returncode)


if __name__ == "__main__":
    nbscript(argv=sys.argv[1:])
