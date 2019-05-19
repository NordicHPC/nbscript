#!/usr/bin/env python3

import argparse
import logging
import os
import re
import shlex
import subprocess
import sys
import time

LOG = logging.getLogger('nbscript')
logging.lastResort.setLevel(logging.DEBUG)

def snotebook(argv=sys.argv[1:]):
    if os.environ.get('NBSCRIPT_RUNNING') is not None:
        LOG.critical("Detected that we are already in snotebook... not executing again.")
        exit(0)

    parser_outer = argparse.ArgumentParser(usage="snotebook [slurm args [--- nbscript args] notebook [nb_argv ...]")
    #parser_outer.add_argument("--output", help="Output filename (basename, no extension).  Default=timestamped output in current dir.")
    #parser_outer.add_argument("--to", help="Convert to this format (same as nbconvert --to option).")
    #parser_outer.add_argument("--export", "-e", action='append', help="Set environment variable (format NAME=VALUE)")
    parser_outer.add_argument("--srun", action='store_true', help="Run with srun (blocking until complete), not sbatch.  Output to stdout if --output not given.")
    parser_outer.add_argument("--raw", action='store_true', help="Don't run with slurm, direct execution")
    parser_outer.add_argument("--verbose", "-v", action="store_true",
                              help="Verbose.")
    parser_outer.add_argument("notebook", help="Input notebook")
    parser_outer.add_argument("argv", nargs=argparse.REMAINDER, help="Output filename (basename, no extension)")

    args, slurm_or_nbscript_args = parser_outer.parse_known_args(argv)
    #args_inner, remaining2 = parser_inner.parse_known_args()

    if args.verbose:
        LOG.setLevel(logging.DEBUG)
    LOG.debug('args: %s', args)
    LOG.debug('slurm_or_nbscript_args: %s', slurm_or_nbscript_args)

    options_slurm    = [ ]
    options_nbscript = [ ]


    # Create the nbscript command line
    #cmd_nbscript = ['jupyter', 'nbconvert', args.notebook,
    #                 '--execute', '--allow-errors', '--ExecutePreprocessor.timeout=None',
    #                 '--to', args.to,
    #                 '--output', output_basename, ]
    #if args.to:
    #    cmd_nbscript.extend(['--to', args.to])
    #if args.output:
    #    cmd_nbscript.extend(['--output', args.output])
    #else:
    #     if '--srun' not in slurm_or_nbscript_args:
    #         cmd_nbscript.extend(['--stdout', ])
    #     else:
    #         cmd_nbscript.extend(['--output=.'])
    if args.verbose:
        options_nbscript.extend(['--verbose'])
    #if args.to:
    #    cmd_nbscript.extend(['--to='+args.to])

    # Find slurm args from within notebook itself.  #SBATCH in the first
    # code cell (only the first).
    import nbformat
    nb = nbformat.read(args.notebook, as_version=4)
    for cell in nb['cells']:
        if cell['cell_type'] != 'code': continue
        source = cell['source']
        for m in re.finditer("^#SBATCH (.*)", source, re.M):
            options_slurm.extend(shlex.split(m.group(1)))
        break

    # Env vars from --export on the command line
    #if args.export:
    #    for keyval in args.export:
    #        cmd_slurm.extend(['--export', keyval+',ALL'])

    # Add in extra options from command line
    if '---' in slurm_or_nbscript_args:
        split_idx = slurm_or_nbscript_args.index('---')
        options_slurm    += slurm_or_nbscript_args[:split_idx]
        options_nbscript += slurm_or_nbscript_args[split_idx+1:]
    else:
        options_slurm += slurm_or_nbscript_args

    if args.verbose:
        LOG.debug('cmd_slurm: %s', cmd_slurm)
        LOG.debug('cmd_nbscript: %s', cmd_nbscript)

    cmd_nbscript = ['nbscript',
                    *options_nbscript,
                    args.notebook,
                    *args.argv,
                    ]

    # Create the slurm command to run
    if args.srun:
        cmd_slurm = ['srun', 'bash', ]
    else:
        cmd_slurm = ['sbatch', '-o', 'snotebook.slurm.out' ]

    cmd_slurm.extend(options_slurm)

    batch_command = """\
#!/bin/bash
ml list
set -x
{nbscript}
""".format(nbscript=" ".join(shlex.quote(x) for x in cmd_nbscript))

    LOG.debug('cmd_slurm: %s', batch_command)

    env = dict(os.environ)
    env.pop('SLURM_JOB_ID', None)  # remove jobid so that this won't be a job step
    env.pop('SLURM_JOBID', None)   # (same)
    #env['NBSCRIPT_RUNNING'] = 'True'
    #env['SNOTEBOOK_INPUT'] = args.notebook
    #env['SNOTEBOOK_OUTPUT'] = output_basename

    if args.raw:
        cmd_slurm = ["bash"]

    p = subprocess.Popen(cmd_slurm, stdin=subprocess.PIPE, env=env)
    p.stdin.write(batch_command.encode())
    p.stdin.close()
    p.wait()

    LOG.debug('snotebook completed, return value %d', p.returncode)
    #print("Output will be in {output_basename}.*".format(output_basename=output_basename))


if __name__ == "__main__":
    snotebook(argv=sys.argv[1:])
