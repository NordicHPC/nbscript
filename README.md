# Run Jupyter notebooks as scripts

Jupyter notebooks are designed almost exclusively for interactive use, but
many people want to use them for heavy-duty computational usage.
`nbscript` is designed to process notebooks as scripts and provide the
most common script features: clear start and end, arguments (argv),
(stdin) and stdout, and so on.

We also take the perspective of batch processing, so also have a wrapper
that allows you to submit notebooks as Slurm scripts (similar sbatch
with a Python as the interpreter).

Notebooks are very good for interactive work, but for large
computation interactive just isn't an efficient use of resources.  For
other expensive resources that can't be shared (GPUs for example),
interactive work even for development can be a bit questionable.  A
proper course of action would be to create proper programs to run
separate from notebooks... but sometimes people prefer to stay in
notebooks.

Many other modules (see references below) try to allow notebooks to be
run, but we take the viewpoint that the traditional UNIX script
interface is good and notebooks should be made like scripts: `nbscript
notebook.ipynb` should behave similarly to `python notebook.py`.  This
also allows us to provide a logical pathway to non-notebook programs.



## Quick examples of invocation

`nbscript`:

* `nbscript input.ipynb [argv]`: runs, prints results as asciidoc to
  stdout.  Within the script, `from nbscript import argv` to get the
  argv.

* `nbscript --save input.ipynb`: runs, saves to `input.out.ipynb`

* `nbscript --save --timestamp input.ipynb`: runs, saves to
  `input.out.TIMESTAMP.ipynb`

`snotebook`:

* `snotebook [slurm opts] input.ipynb`: submits to slurm with
  `sbatch`, using the `--save` option like you see above.  Slurm
  output is in `input.out.ipynb.log`.

* `snotebook [slurm opts] --- --timestamp input.ipynb`: like above,
  but adds `--timestamp` option like you see above.



## Usage

nbscript is still in development, so not all of this functionality
exists yet.  In general, `nbscript notebook.ipynb` should have as
similar an interface as `python notebook.py`.


Run a notebook from the command line:

* `nbscript nb.ipynb arg1 arg2 ...`.  Within the notebook, you can
  access the arguments by `import nbscript ; nbscript.argv` (these are
  currently transferred via environment variables).  Note that `argv[0]`
  is the notebook name if it is known, otherwise `None`.

* By default, only the output of the cells is printed to stdout.
  Options may used to save the notebook to a file in any of
  nbconvert's supported output formats.


You may also run a notebook via IPython extensions:

* `%nbscript nb.ipynb [arg1 arg2 ...]`.  By default the output isn't
  substituted back in, because we couldn't do much with that.
  Instead, it is saved to a HTML file with the output and errors.  If
  you don't give an output name, the output is timestamped.

  * Currently not implemented, use `!nbscript` instead.

* `nbscript` sets the `NBSCRIPT_RUNNING` environment variable, and if
  this is already set it won't run again.  That way, you can have a
  notebook execute itself with the `%nbscript`magic function.


Interface within notebooks:

* `import nbscript ; nbscript.argv` is the `argv` in analogy to
  `sys.argv`.  (json-encoded in the environment variable `NB_ARGV`).

  * One would use `argparse` with `nbscript.argv`, in particularly
    `parser.parse_args(args=nbscript.argv[1:])`.

* Other environment variables: `NB_NAME` is the notebook name (note
  that there is no way for Jupyter kernels to know the currently
  executing notebook name, this seems to be intentional because it's a
  protocol layer violation).

* `nbscript` sets the environment variable `NBSCRIPT_RUNNING` before
  it executes a notebook, and if this is already set then it will do
  nothing if it tries to execute again (print an error message and
  exit).  This is so that an notebook can `nbscript`-execute itself
  without recursive execution.  This behavior is up for debate.


Submit a notebook via Slurm

* `snotebook nb.ipynb arg1 arg2`.  This is similar to `sbatch
  script.sh arg1 arg2` - it will search for `#SBATCH` lines and
  process them (stopping the search after the first cell that has
  any).

* Similar to the `%nbscript` magic function, there is the `%snotebook`
  magic function.


Saving output state:

* When a notebook is run non-interactively, it would be useful to save
  the state so that the output variables can be re-loaded and played
  with.  To do that, we should find some way to serialize the state
  and re-load it.  It would be nice if nbscript could automate this,
  but perhaps that makes things too fragile.

* The [dill](https://pypi.org/project/dill/) module is supposed to be
  able to serialize most Python objects (but starts failing at some
  complex machine learning pipeline objects).  One can try to
  serialize the state at the end of the execution.

* In the future, we want to add support for automatically serializing
  the final state after the notebook is run in parallel to the html
  output.  This would allow one to re-load the state to continue
  post-processing.  For now, though, we recommend you explicitly save
  whatever is important (this is probably more reliable anyway).



## See also

There are many commands to execute notebooks, but most of these do not
see the notebooks as a first-class script, but as an interactive thing
which happens to be run.  that would have run, arguments, stdout, etc.


* https://github.com/nteract/papermill seems to be one of the most
  similar projects to this.  Cells are tagged as containing
  parameters, which means that they can be overridden from the command
  line. It still takes the view that this is mainly a notebook.

* [nbconvert](https://nbconvert.readthedocs.io/en/latest/) is the
  default way for executing notebooks.  There is no default way to
  pass arguments and output formats are designed to look like
  notebooks.

* https://pypi.org/project/runipy/ is a pretty basic script similar to
  `nbconvert --execute` it seems (deprecated in favor of `nbconvert
  --execute`).

* Several tools called `nbrun`, some of which are deprecated in favor
  of `nbconvert`.

* https://github.com/takluyver/nbparameterise also dynamically
  replaces values in cells.

* https://github.com/NERSC/slurm-magic is IPython magic functions for
  interacting with Slurm.  It doesn't do anything special about the
  notebook format.  The `%%sbatch` magic submits a cell as a Slurm
  shell script and probably the `%srun` magic runs a command line.
  This makes a logical companion to `nbscript` and is perhaps better
  than an interface we might make.

* and many more...

All of these accomplish the same thing but have different (a few) or
no (most) ways of passing parameters.



## Development status and maintnance

Currently this is a usable alpha - the main invocations work, but get
too creative and expect problems!  There are tests to verify the
important stuff works, though.

Maintainer: Richard Darst, Aalto University.  Feedback and
improvements encouraged.