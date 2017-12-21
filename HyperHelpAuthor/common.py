import sublime

import os
import textwrap

from hyperhelp.common import log, hh_syntax


###----------------------------------------------------------------------------


def plugin_loaded():
    """
    Do package setup at packge load time.
    """
    hha_setting.obj = sublime.load_settings("HyperHelpAuthor.sublime-settings")
    hha_setting.default = {
        "update_header_on_save": True,
        "author_view_settings": {
            "rulers": [80],
            "match_selection": True,
            "draw_indent_guides": True
        }
    }


###----------------------------------------------------------------------------


def hha_setting(key):
    """
    Get a HyperHelpAuthor setting from a cached settings object.
    """
    default = hha_setting.default.get(key, None)
    return hha_setting.obj.get(key, default)


def is_authoring_source(view):
    """
    Given a view object, tells you if that view represents a help source file.
    """
    if view.match_selector(0, "text.hyperhelp.help"):
        return not view.is_read_only()

    return False


def local_help_filename(pkg_info, help_file):
    """
    Determine what the full file name of a help file from a given package would
    be if it was stored locally
    """
    return os.path.join(sublime.packages_path(), pkg_info.doc_root, help_file)


def format_template(template, *args):
    """
    Given incoming text, remove all common indent, then strip away the leading
    and trailing whitespace from it.

    This is a modified version of code from Default/new_templates.py from the
    core Sublime code.
    """
    return textwrap.dedent(template % args).strip()


def open_local_help(pkg_info, help_file, window=None):
    """
    Attempt to open the provided help file locally for editing.
    """
    window = window if window is not None else sublime.active_window()
    local_path = local_help_filename(pkg_info, help_file)

    if not os.path.exists(local_path):
        return log(format_template(
            """
            Specified help file does not exist; cannot open.

            Note: HyperHelpAuthor can not currently open help
            files from packed packages for editing.
            """), dialog=True)

    view = window.open_file(local_path)
    view.settings().set("_hh_auth", True)
    if not view.is_loading():
        apply_authoring_settings(view)


def open_help_index(pkg_info, window=None):
    """
    Attempt to open the provided help index file localy for editing.
    """
    window = window if window is not None else sublime.active_window()

    # The index file is stored as a resource file spec, so strip the prefix
    local_path = os.path.join(sublime.packages_path(),
                              pkg_info.index_file[len("Packages/"):])

    if not os.path.exists(local_path):
        return log(format_template(
            """
            Specified help index does not exist; cannot open.

            Note: HyperHelpAuthor can not currently open help
            indexes from packed packages for editing.
            """), dialog=True)

    window.open_file(local_path)


def apply_authoring_settings(view):
    """
    Given a view, apply the appropriate settings to it to ensure that it is set
    up properly for editing.
    """
    # Ensure help files with no header get the appropriate syntax set
    view.assign_syntax(hh_syntax("HyperHelp.sublime-syntax"))

    author_view_settings = hha_setting("author_view_settings")
    settings = view.settings()
    for option in author_view_settings:
        settings.set(option, author_view_settings[option])


###----------------------------------------------------------------------------
