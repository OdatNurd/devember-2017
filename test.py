import sublime
import sublime_plugin


from .core import log, hh_syntax
from .view import update_help_view

###----------------------------------------------------------------------------


class HelpTestCommand(sublime_plugin.WindowCommand):
    def run(self):
        help_file = "Packages/hyperhelp/help/sample.txt"
        try:
            help_txt = sublime.load_resource(help_file)
        except:
            help_txt = "Unable to load help text"

        update_help_view(help_txt, "hyperhelp", "sample.txt",
                         hh_syntax("HyperHelp.sublime-syntax"))


###----------------------------------------------------------------------------
