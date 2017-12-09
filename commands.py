import sublime
import sublime_plugin

import os

from .common import log
from .view import focus_on
from .core import help_index_list, reload_help_index
from .core import show_help_topic, display_help_file, reload_help_file


###----------------------------------------------------------------------------


class HyperhelpReloadHelpCommand(sublime_plugin.TextCommand):
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


class HyperhelpReloadIndexCommand(sublime_plugin.TextCommand):
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
            log("Index not previously reloaded; reloading indexes", status=True)
            package = None
        else:
            log("Reloading help index for package '%s'", package, status=True)

        reload_help_index(help_index_list(), package)

    def is_enabled(self):
        return (self.view.match_selector(0, "text.hyperhelp.index") and
                self.view.file_name() is not None)


class HyperhelpNavigateCommand(sublime_plugin.TextCommand):
    """
    Perform navigation from within a help file
    """
    available_nav = ["find_anchor", "follow_link"]

    def run(self, edit, nav, prev=False):
        if nav == "find_anchor":
            return self.anchor_nav(prev)

        return self.follow_link()

    def is_enabled(self, nav, prev=False):
        settings = self.view.settings()
        return (nav in self.available_nav and
                settings.has("_hh_pkg") and settings.has("_hh_file"))

    def anchor_nav(self, prev):
        anchors = self.view.settings().get("_hh_nav")
        if not anchors:
            return

        point = self.view.sel()[0].begin()
        fallback = anchors[-1] if prev else anchors[0]

        pick = lambda p: (point < p[1][0]) if not prev else (point > p[1][0])
        for pos in reversed(anchors) if prev else anchors:
            if pick(pos):
                return focus_on(self.view, pos[1])

        focus_on(self.view, fallback[1])

    def follow_link(self):
        point = self.view.sel()[0].begin()
        if self.view.match_selector(point, "text.hyperhelp meta.link"):
            topic = self.view.substr(self.view.extract_scope(point))

            package = self.view.settings().get("_hh_pkg")
            show_help_topic(package, topic)


###----------------------------------------------------------------------------
