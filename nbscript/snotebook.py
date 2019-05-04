#!/usr/bin/env python3

import argparse
import os
import re
import shlex
import subprocess
import time


def main():
    if os.environ.get('NBSCRIPT_RUNNING') is not None:
        print("Detected that we are already in snotebook... not executing again.")
        exit(0)

    parser_outer = argparse.ArgumentParser(usage="snotebook [slurm args [--- nbconvert args] notebook [nb_argv ...]")
    parser_outer.add_argument("notebook", help="Input notebook")
    parser_outer.add_argument("--output", help="Output filename (basename, no extension).  Default=timestamped output in current dir.")
    parser_outer.add_argument("--to", help="Convert to this format (same as nbconvert --to option).")
    parser_outer.add_argument("--export", "-e", action='append', help="Set environment variable (format NAME=VALUE)")
    parser_outer.add_argument("--srun", action='store_true', help="Run with srun (blocking until complete), not sbatch.  Output to stdout if --output not given.")
    parser_outer.add_argument("--raw", action='store_true', help="Don't run with slurm, direct execution")
    parser_outer.add_argument("--verbose", "-v", action="store_true",
                              help="Verbose.")
    parser_outer.add_argument("argv", nargs=argparse.REMAINDER, help="Output filename (basename, no extension)")

    # These arguments are parsed but passed on to srun.
    #parser_inner = argparse.ArgumentParser()

    args, slurm_or_nbconvert_args        = parser_outer.parse_known_args()
    #args_inner, remaining2 = parser_inner.parse_known_args()

    if args.verbose:
        print(args)
        print('slurm_or_nbconvert_args:', slurm_or_nbconvert_args)
        #print(args_inner, remaining2)

    ##output_basename = args.notebook+'`date +%Y-%m-%d_%H:%M:%S`'
    #if args.output:
    #    output_basename = args.output
    #else:
    #    basename, ext = os.path.splitext(args.notebook)
    #    if ext == '.ipynb':
    #        basename = basename
    #    else:
    #        basename = basename + ext
    #    output_basename = basename + time.strftime('.%Y-%m-%d_%H:%M:%S')


    # Create the slurm command to run
    if args.srun:
        cmd_slurm = ['srun', ]  # "bash" appended later
    else:
        cmd_slurm = ['sbatch', '-o', 'snotebook.slurm.out' ]

    # Create the nbconvert command line
    #cmd_nbconvert = ['jupyter', 'nbconvert', args.notebook,
    #                 '--execute', '--allow-errors', '--ExecutePreprocessor.timeout=None',
    #                 '--to', args.to,
    #                 '--output', output_basename, ]
    cmd_nbconvert = ['nbscript',
                     '--timestamp',
                    ]
    #if args.to:
    #    cmd_nbconvert.extend(['--to', args.to])
    if args.output:
        cmd_nbconvert.extend(['--output', args.output])
    else:
         if '--srun' not in slurm_or_nbconvert_args:
             cmd_nbconvert.extend(['--stdout', ])
         else:
             cmd_nbconvert.extend(['--output=.'])
    if args.verbose:
        cmd_nbconvert.extend(['--verbose'])
    if args.to:
        cmd_nbconvert.extend(['--to='+args.to])
    cmd_nbconvert.extend([args.notebook] + args.argv)

    # Find slurm args from within notebook itself.  #SBATCH in the first
    # code cell (only the first).
    import nbformat
    nb = nbformat.read(args.notebook, as_version=4)
    for cell in nb['cells']:
        if cell['cell_type'] != 'code': continue
        source = cell['source']
        for m in re.finditer("^#SBATCH (.*)", source, re.M):
            cmd_slurm.extend(shlex.split(m.group(1)))
        break

    # Env vars from --export on the command line
    if args.export:
        for keyval in args.export:
            cmd_slurm.extend(['--export', keyval+',ALL'])

    # Add in extra options from command line
    if '---' in slurm_or_nbconvert_args:
        split_idx = slurm_or_nbconvert_args.index('---')
        cmd_slurm     += slurm_or_nbconvert_args[:split_idx]
        cmd_nbconvert += slurm_or_nbconvert_args[split_idx+1:]
    else:
        cmd_slurm += slurm_or_nbconvert_args

    if args.srun:
        cmd_slurm.append('bash')

    if args.verbose:
        print(cmd_slurm)
        print(cmd_nbconvert)

    batch_command = """\
#!/bin/bash
ml list
set -x
{nbconvert}
""".format(nbconvert=" ".join(shlex.quote(x) for x in cmd_nbconvert))

    if args.verbose:
        print(batch_command)

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

    #print("Output will be in {output_basename}.*".format(output_basename=output_basename))


if __name__ == "__main__":
    main()
