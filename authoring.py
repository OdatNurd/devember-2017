import sublime
import sublime_plugin

import os

from .common import log, current_help_package
from .core import help_index_list
from .core import reload_help_file


###----------------------------------------------------------------------------


class HyperhelpAuthorReloadHelpCommand(sublime_plugin.TextCommand):
    """
    If the current view is a hyperhelp help view, this will reload the file
    currently being displayed in the view.
    """
    def run(self, edit):
        help_file = self.view.settings().get("_hh_file", None)
        if reload_help_file(help_index_list(), self.view):
            log("Reloaded help file '%s'", help_file, status=True)

    def is_enabled(self):
        settings = self.view.settings()
        return settings.has("_hh_pkg") and settings.has("_hh_file")


class HyperhelpAuthorReloadIndexCommand(sublime_plugin.TextCommand):
    """
    If the current view is a hyperhelp index view, this will attempt to reload
    the help index so that the current changes will immediately take effect.
    """
    def run(self, edit):
        filename = os.path.realpath(self.view.file_name())
        if not filename.startswith(sublime.packages_path()):
            return log("Cannot reload help index; not in package", status=True)

        filename = os.path.relpath(filename, sublime.packages_path())
        package = os.path.split(filename)[0].split(os.sep)[0]

        if package not in help_index_list():
            log("Package index for '%s' not previously loaded; reloading all indexes",
                package, status=True)
            package = None
        else:
            log("Reloading help index for package '%s'", package, status=True)

        help_index_list(reload=True, package=package)

    def is_enabled(self):
        return (self.view.match_selector(0, "text.hyperhelp.index") and
                self.view.file_name() is not None)


###----------------------------------------------------------------------------
