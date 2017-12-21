import sublime
import sublime_plugin

import os

from .common import log
from .core import load_help_index, display_help_file
from .authoring import _global_package_list


###----------------------------------------------------------------------------


def _test_help():
    help_index = load_help_index("Packages/hyperhelp/help/hyperhelp.json")
    for topic, entry in help_index.help_topics.items():
        log("'%s': '%s'", topic, entry["file"])


def _help_load_index():
    index_res = os.path.join(sublime.packages_path(),
                             "hyperhelp", "help", "hyperhelp.json")
    info = load_help_index(index_res)
    if info:
        from pprint import pformat

        log("Loaded index for package: '%s'", info.package)
        log("Index loaded from: '%s'", info.index_file)
        log("Help description: '%s'", info.description)
        log("Document root: '%s'", info.doc_root)
        log("Available help topics:\n%s", pformat(info.help_topics))
        log("Help Files: '%s'", info.help_files)
        log("Package Files: '%s'", info.package_files)
        log("URLs: '%s'", info.urls)
        log("Package TOC:\n%s", pformat(info.help_toc))
    else:
        log("Unable to load help index")

###----------------------------------------------------------------------------

class HelpTestCommand(sublime_plugin.WindowCommand):
    def run(self):
        _test_help()
        # _help_load_index()
        # for pkg in _global_package_list():
        #     print(pkg)


###----------------------------------------------------------------------------
