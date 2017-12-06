import sublime
import sublime_plugin

from .core import log
from .help import display_help
from .help_index import _load_help_index

###----------------------------------------------------------------------------


class HelpTestCommand(sublime_plugin.WindowCommand):
    def run(self):
        print(_load_help_index("hyperhelp", "Packages/hyperhelp/help/hyperhelp.json"))
        # display_help("Packages/hyperhelp/help/sample.txt")


###----------------------------------------------------------------------------
