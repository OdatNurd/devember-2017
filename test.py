import sublime
import sublime_plugin

from .core import log
from .help import display_help

###----------------------------------------------------------------------------


class HelpTestCommand(sublime_plugin.WindowCommand):
    def run(self):
        display_help("Packages/hyperhelp/help/sample.txt")


###----------------------------------------------------------------------------
