import sublime

from .view import find_help_view


###----------------------------------------------------------------------------


def log(message, *args, status=False, dialog=False):
    """
    Log the provided message to the console, optionally also sending it to the
    status bar and a dialog box.
    """
    message = message % args
    print("HyperHelp:", message)
    if status:
        sublime.status_message(message)
    if dialog:
        sublime.message_dialog(message)


def hh_syntax(base_file):
    """
    Return the syntax file associated with the given base syntax file name.
    This can return None if the syntax is not known.
    """
    syn_list = sublime.find_resources(base_file)
    if len(syn_list) == 1:
        return syn_list[0]

    log("Unable to locate unique syntax '%s'", base_file)


def current_help_package(view=None, window=None):
    """
    Obtain the package that contains the currently displayed help file or None
    if help is not visible.

    Looks in the help view provided, or the help view in the passed in window,
    or the help view in the currently active window.
    """
    view = view or find_help_view(window)
    return (view.settings().get("_hh_pkg") if view is not None else None)


###----------------------------------------------------------------------------
