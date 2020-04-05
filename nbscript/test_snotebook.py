# pylint: disable=unused-argument,redefined-outer-name
import logging

from . import snotebook
from .testutil import tdir_slurm, assert_sublist

from .nbscript import LOG as nbscript_LOG
nbscript_LOG.setLevel(logging.DEBUG)

def test_snotebook_basic(tdir_slurm, monkeypatch):
    def sbatch(cmd_submit, stdin, env, cmd_nbscript):
        assert '--mem=1234M' in cmd_submit
        assert '--gres=gpu:1' in cmd_submit
        assert_sublist(cmd_submit, ['-c', '5'])
        assert '--invalid-argument' not in cmd_submit

    monkeypatch.setattr(snotebook, "execute_sbatch", sbatch)
    snotebook.snotebook(['slurm.ipynb'])


def test_batch(tdir_slurm, monkeypatch):
    """snotebook slurm.ipynb should do:

    results in slurm.out.ipynb
    stdout in  slurm.out.ipynb.log
    """
    def sbatch(cmd_submit, stdin, env, cmd_nbscript):
        assert '--save' in cmd_nbscript
        assert '--output=slurm.out.ipynb.log' in cmd_submit
        assert '--mem=1234M' in cmd_submit
    monkeypatch.setattr(snotebook, "execute_sbatch", sbatch)
    snotebook.snotebook(['slurm.ipynb'])

def test_batch_timestamp(tdir_slurm, monkeypatch):
    """snotebook --timestamp slurm.ipynb should do:

    results in slurm.out.TS.ipynb
    stdout in  slurm.out.TS.ipynb.log
    """
    def sbatch(cmd_submit, stdin, env, cmd_nbscript):
        assert '--timestamp' in cmd_nbscript
        assert '--save' in cmd_nbscript
        assert '--output=slurm.out.ipynb.log' in cmd_submit
        assert '--mem=1234M' in cmd_submit
    monkeypatch.setattr(snotebook, "execute_sbatch", sbatch)
    snotebook.snotebook(['---', '--timestamp', 'slurm.ipynb'])
