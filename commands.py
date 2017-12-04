import sublime
import sublime_plugin

from .view import focus_on
from .help import display_help


###----------------------------------------------------------------------------


class HyperHelpReloadHelpCommand(sublime_plugin.TextCommand):
    """
    If the current view is a hyperhelp help view, this will reload the file
    currently being displayed in the view.
    """
    def run(self, edit):
        settings = self.view.settings()
        pkg = settings.get("_hh_pkg")
        file = settings.get("_hh_file")

        res_file = "Packages/%s/help/%s" % (pkg, file)

        settings.set("_hh_file", "")
        display_help(res_file)

    def is_enabled(self):
        settings = self.view.settings()
        return settings.has("_hh_pkg") and settings.has("_hh_file")


class HyperHelpNavigateCommand(sublime_plugin.TextCommand):
    """
    Perform navigation from within a help file
    """
    available_nav = ["find_anchor"]

    def run(self, edit, nav, prev=False):
        if nav == "find_anchor":
            return self.anchor_nav(prev)

    def is_enabled(self, nav, prev=False):
        return nav in self.available_nav

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


###----------------------------------------------------------------------------
