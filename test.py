import sublime
import sublime_plugin

from .core import log
from .help import display_help
from .help_index import _load_help_index

###----------------------------------------------------------------------------


class HelpTestCommand(sublime_plugin.WindowCommand):
    def run(self):
        info = _load_help_index("hyperhelp", "Packages/hyperhelp/help/hyperhelp.json")
        log("%s", info if info is not None else "Help index not loaded")
        # display_help("Packages/hyperhelp/help/sample.txt")


###----------------------------------------------------------------------------
