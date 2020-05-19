# Copied from the nbgrader validate extension:
#   https://github.com/jupyter/nbgrader/blob/4c5d6f606c8a2ec7b51e05f7f08797be6252f7f5/nbgrader/server_extensions/validate_assignment/handlers.py
#   https://github.com/jupyter/nbgrader/blob/master/nbgrader/server_extensions/validate_assignment/handlers.py
# License: BSD 3-Clause

# Relevant documentation:
#   https://jupyter-notebook.readthedocs.io/en/stable/extending/handlers.html

import json
import os
import subprocess

from tornado import web
from traitlets import Bool, List, Unicode, Union, HasTraits
from traitlets.config import Configurable
#from traitlets import Application

from jupyter_core.paths import jupyter_config_path
from notebook.utils import url_path_join as ujoin
from notebook.base.handlers import IPythonHandler


# This does NOT yet work!
class NBScriptBatch(Configurable):
    """Configuration for nbscript batch extension.

    In jupyter_notebook_config.py, you can set, for example::

        c.NBScriptBatch.batch_command = ['x', 'y']

    """
    batch_command = Union([List(['nbscript', '--save', '--timestamp']),
                           Unicode("")],
                          help="Configure batch command").tag(config=True)
    asynchronous = Bool(False)


class NbscriptBatchHandler(IPythonHandler):

    # jupyter notebook --JupyterBatch.batch_command="xxx"
    #batch_command = Union([List(['nbscript', '--save', '--timestamp']), Unicode("")],
    #                       help="Configure batch command").tag(config=True)
    batch_command = ['nbscript', '--save', '--timestamp']
    asynchronous = False

    @web.authenticated
    def get(self):
        """Do the processing

        TODO: change to POST later

        HTTP arguments:
             path:  relative path to command

        HTTP return body:
            JSON object
        """
        print('setting', NBScriptBatch().batch_command)

        # get_argument returns both GET query arguments and POST body arguments
        path = self.get_argument('path')
        # request body: self.request.body

        fullpath = os.path.join(self.settings['notebook_dir'], path)
        # print('a'*10, fullpath)

        base_cmd = self.batch_command
        # print('b'*10, base_cmd)
        if isinstance(base_cmd, str):
            # String command: substitute {} for fullpath
            if '{path}' in base_cmd:
                cmd = base_cmd.format(path=fullpath)
            else:
                # if no '{}' in the string, just appendit
                cmd = base_cmd + ' ' + fullpath
        else:
            # If list command, substitute '{}', and if that doesn't
            # exist in any arguments, append it.
            if any('{path}' in x for x in base_cmd):
                cmd = [x.format(path=fullpath) for x in base_cmd]
            else:
                cmd = base_cmd + [fullpath]

        print('c'*10, cmd)
        ret = {
            'fullpath': fullpath,
            'cmd': cmd,
            'asynchronous': self.asynchronous,
            }

        # Run the process
        if self.asynchronous:
            subprocess.call(cmd)
        else:
            # Run in foreground, capture output and so on
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
            out, _ = p.communicate()
            ret['stdouterr'] = out.decode(errors='backslashreplace')
            ret['returncode'] = p.returncode

        # self.set_status(401)
        self.finish(json.dumps(ret))


handlers = [
    (r"/nbscript/batch", NbscriptBatchHandler),
    ]


def load_jupyter_server_extension(nbapp):
    """Jupyter server-extension load hook"""
    nbapp.log.info("Loading the nbscript batch server extension")
    webapp = nbapp.web_app
    base_url = webapp.settings['base_url']
    webapp.settings['notebook_dir'] = nbapp.notebook_dir
    webapp.add_handlers(".*$", [
        (ujoin(base_url, pat), handler)
        for pat, handler in handlers
    ])
