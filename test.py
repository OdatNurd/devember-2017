import sublime
import sublime_plugin

from .common import log

from .core import load_help_index, display_help_file

###----------------------------------------------------------------------------


def _test_help():
    help_index = load_help_index("Packages/hyperhelp/help/hyperhelp.json")
    display_help_file(help_index, "index.txt")


def _help_load_index():
    info = load_help_index("Packages/hyperhelp/help/hyperhelp.json")
    if info:
        from pprint import pformat

        log("Loaded index for package: '%s'", info.package)
        log("Index loaded from: '%s'", info.index_file)
        log("Help description: '%s'", info.description)
        log("Document root: '%s'", info.doc_root)
        log("Available help topics:\n%s", pformat(info.help_topics))
        log("Package TOC:\n%s", pformat(info.help_toc))

###----------------------------------------------------------------------------


class HelpTestCommand(sublime_plugin.WindowCommand):
    def run(self):
        _test_help()
        # _help_load_index()


###----------------------------------------------------------------------------
