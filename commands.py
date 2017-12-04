import sublime
import sublime_plugin

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


###----------------------------------------------------------------------------
