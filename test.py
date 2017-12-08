import sublime
import sublime_plugin

from .common import log

from .core import display_help
from .help_index import _load_help_index

###----------------------------------------------------------------------------


def _test_help():
    display_help("Packages/hyperhelp/help/sample.txt")


def _help_load_index():
    info = _load_help_index("Packages/hyperhelp/help/hyperhelp.json")
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
        # _test_help()
        _help_load_index()


###----------------------------------------------------------------------------
