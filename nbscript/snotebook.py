#!/usr/bin/env python3

import argparse
import logging
import os
import re
import shlex
import subprocess
import sys
try:
    from shlex import quote as shlex_quote
except ImportError:
    from pipes import quote as shlex_quote


from . import nbscript

LOG = logging.getLogger('nbscript.snotebook')
logging.lastResort.setLevel(logging.DEBUG)


def snotebook(argv=sys.argv[1:]):
    if os.environ.get('NBSCRIPT_RUNNING') is not None:
        LOG.critical("Detected that we are already in snotebook... not executing again.")
        sys.exit(0)

    parser_outer = argparse.ArgumentParser(usage="snotebook [slurm args [--- nbscript args] notebook [nb_argv ...]")
    parser_outer.add_argument("--srun", action='store_true',
                              help="Run with srun (blocking until complete), not sbatch.  Output to stdout if --output not given.")
    parser_outer.add_argument("--raw", action='store_true',
                              help="Don't run with slurm, direct execution")
    parser_outer.add_argument("--verbose", "-v", action="store_true",
                              help="Verbose.")
    parser_outer.add_argument("notebook",
                              help="Input notebook")
    parser_outer.add_argument("argv", nargs=argparse.REMAINDER,
                              help="arguments of the notebook itself.")

    args, slurm_or_nbscript_args = parser_outer.parse_known_args(argv)
    #args_inner, remaining2 = parser_inner.parse_known_args()

    if args.verbose:
        LOG.setLevel(logging.DEBUG)
    LOG.debug('args: %s', args)
    LOG.debug('slurm_or_nbscript_args: %s', slurm_or_nbscript_args)

    options_slurm    = [ ]
    options_nbscript = [ ]

    if args.verbose:
        options_nbscript.extend(['--verbose'])

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
    LOG.debug('options_slurm: %s', options_slurm)

    # Add in extra options from command line. '---' separates slurm options and
    # nbscript options.  If this doesn't exist, everything is nbscript options.
    if '---' in slurm_or_nbscript_args:
        split_idx = slurm_or_nbscript_args.index('---')
        options_slurm    += slurm_or_nbscript_args[:split_idx]
        options_nbscript += slurm_or_nbscript_args[split_idx+1:]
    else:
        options_slurm += slurm_or_nbscript_args
    LOG.debug('options_slurm: %s', options_slurm)
    LOG.debug('options_nbscript: %s', options_nbscript)

    def make_cmd_nbscript():
        return ['nbscript',
                ] + options_nbscript + [
                args.notebook,
                ] + args.argv
    cmd_nbscript = make_cmd_nbscript()
    LOG.debug('cmd_nbscript: %s', cmd_nbscript)

    # This invokes nbscript as a parser, doesn't run anything but returns all
    # of the properties.
    nbscript_locals = nbscript.nbscript(cmd_nbscript[1:],
                                        _return_names=True)
    LOG.debug('nbscript_locals: %s', nbscript_locals)

    # If there is no output filename, then we need to --save it.
    if not (args.srun or args.raw):
        if not nbscript_locals['output_fname']:
            options_nbscript.append('--save')
            cmd_nbscript = make_cmd_nbscript()
            LOG.debug('cmd_nbscript: %s', cmd_nbscript)
            nbscript_locals = nbscript.nbscript(cmd_nbscript[1:],
                                                _return_names=True)
            LOG.debug('nbscript_locals: %s', nbscript_locals)
    LOG.debug('cmd_nbscript: %s', cmd_nbscript)

    # Create the slurm command to run
    if args.srun:
        cmd_submit = ['srun', 'bash', ]
    elif args.raw:
        cmd_submit = ["bash"]
    else:
        cmd_submit = ['sbatch']
        if nbscript_locals['args'].save:
            options_slurm.extend(['--output='+nbscript_locals['output_fname_before_timestamp']+'.log'])

    cmd_submit.extend(options_slurm)

    LOG.debug('cmd_submit: %s', cmd_submit)
    LOG.debug('cmd_nbscript: %s', cmd_nbscript)

    batch_command = """\
#!/bin/bash
set -x
{nbscript}
""".format(nbscript=" ".join(shlex_quote(x) for x in cmd_nbscript))

    LOG.debug('cmd_submit: %s', batch_command)

    env = dict(os.environ)
    env.pop('SLURM_JOB_ID', None)  # remove jobid so that this won't be a job step
    env.pop('SLURM_JOBID', None)   # (same)
    #env['NBSCRIPT_RUNNING'] = 'True'
    #env['SNOTEBOOK_INPUT'] = args.notebook
    #env['SNOTEBOOK_OUTPUT'] = output_basename

    retcode = execute_sbatch(cmd_submit, batch_command.encode(), env, cmd_nbscript=cmd_nbscript)

    LOG.debug('snotebook completed, return value %d', retcode)
    return(retcode)

def execute_sbatch(cmd_submit, stdin, env, cmd_nbscript):  # pylint: disable=unused-argument
    """Execute sbatch.  This is separate for mocking during testing"""
    p = subprocess.Popen(cmd_submit, stdin=subprocess.PIPE, env=env)
    p.stdin.write(stdin)
    p.stdin.close()
    p.wait()
    return p.returncode


if __name__ == "__main__":
    snotebook(argv=sys.argv[1:])
