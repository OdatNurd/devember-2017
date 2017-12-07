import sublime
import sublime_plugin

from .core import log
from .help import display_help
from .help_index import _load_help_index

###----------------------------------------------------------------------------


class HelpTestCommand(sublime_plugin.WindowCommand):
    def run(self):
        # display_help("Packages/hyperhelp/help/sample.txt")
        info = _load_help_index("hyperhelp", "Packages/hyperhelp/help/hyperhelp.json")
        if info:
            from pprint import pformat

            log("Loaded index for package: '%s'", info.package)
            log("Index loaded from: '%s'", info.index_file)
            log("Help description: '%s'", info.description)
            log("Document root: '%s'", info.doc_root)
            log("Available help topics:\n%s", pformat(info.help_topics))
            log("Package TOC:\n%s", pformat(info.help_toc))


###----------------------------------------------------------------------------
