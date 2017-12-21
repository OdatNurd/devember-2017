import sublime
import sublime_plugin

from .common import hha_setting, is_authoring_source, apply_authoring_settings


###----------------------------------------------------------------------------


def _apply_author_settings(view):
    """
    If this view has the setting that indicates that this is an authoring view
    that was just opened or created, remove the setting and apply the authoring
    settings to it.
    """
    if view.settings().get("_hh_auth", None) is not None:
        view.settings().erase("_hh_auth")
        apply_authoring_settings(view)


###----------------------------------------------------------------------------


class HyperhelpAuthorEventListener(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        """
        If the file about to be saved is a help file, try to update the date
        in the header.
        """
        _apply_author_settings(view)

        if hha_setting("update_header_on_save") and is_authoring_source(view):
            view.run_command("hyperhelp_author_update_header", {"quiet": True})

    def on_load(self, view):
        """
        If the view is a help file that is marked as being opened by the
        authoring tool, apply the appropriate authoring settings to it to make
        editing easier.
        """
        _apply_author_settings(view)


###----------------------------------------------------------------------------
