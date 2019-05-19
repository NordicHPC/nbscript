# Run Jupyter notebooks as scripts

Jupyter notebooks are designed exclusively for interactive use, but
many people want to use them for heavy-duty computational usage.
`nbscript` is designed to process notebooks as scripts and provide the
most common script functions: clear start and end, arguments (argv),
(stdin) and stdout, and so on.  This takes the view that we provide a
logical transition to non-notebook programs.

We also take the perspective of batch processing, so also have a wrapper
that allows you to submit notebooks as Slurm scripts (similar sbatch
with a Python as the interperter).

## Usage

Not all of this functionality exists yet, but this shows the desired
end state.

Run a notebook from the command line:

* `nbscript nb.ipynb arg1 arg2 ...`.  Within the notebook.  You can
  access the arguments by `import nbscript ; nbscript.argv` (these are
  currently accessed via environment variables).  Note that `argv[0]`
  is the script name if it is known, otherwise `None`.

* By default, only the output of the cells is printed to stdout.
  Options may used to save the notebook to a file in any of
  nbconvert's supported output formats.

You may also run a notebook via IPython extensions:

* `%nbscript nb.ipynb [arg1 arg2 ...]`.  By default the output isn't
  substituted back in, because we couldn't do much with that.
  Instead, it is saved to a HTML file with the output and errors.  If
  you don't give an output name, the output is timestamped.

* `nbscript` sets the `NBSCRIPT_RUNNING` environment variable, and if
  this is already set it won't run again.  That way, you can have a
  notebook execute itself with the `%nbscript`magic function.


Submit a notebook via Slurm

* `snotebook nb.ipynb arg1 arg2`.  This is similar to `sbatch
  script.sh arg1 arg2` - it will search for `#SBATCH` lines and
  process them (stopping the search after the first cell that has
  any).

* Similar to the `%nbscript` magic function, there is the `%snotebook`
  magic function.

Serializing output state:

* It's useful to be able to play with the output variables after batch
  processing, and for that we need to serialize somehow.

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
  `nbconvert --execute` it seems.

* Several tools called `nbrun`, some of which are deprecated in favor
  of `nbconvert`.

* and many more...

All of these accomplish the same thing but have different (a few) or
no (most) ways of passing parameters.