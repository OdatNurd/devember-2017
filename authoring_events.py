import sublime
import sublime_plugin

from .authoring_common import hha_setting, is_authoring_source


###----------------------------------------------------------------------------


class HyperhelpAuthorEventListener(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        """
        If the file about to be saved is a help file, try to update the date
        in the header.
        """
        if hha_setting("update_header_on_save") and is_authoring_source(view):
            view.run_command("hyperhelp_author_update_header", {"quiet": True})


###----------------------------------------------------------------------------
