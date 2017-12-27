import sublime

import codecs

from .view import find_help_view


###----------------------------------------------------------------------------


def log(message, *args, status=False, dialog=False):
    """
    Log the provided message to the console, optionally also sending it to the
    status bar and a dialog box.
    """
    message = message % args
    for line in message.splitlines():
        print("HyperHelp:", line)
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


def load_resource(res_name):
    """
    Attempt to load and decode the UTF-8 encoded string with normalized line
    endings, returning the string on success or None on error.

    This works with regular resource specifications as well as local file names,
    so long as the file is contained in the Sublime package directory.
    """
    try:
        if res_name.startswith(sublime.packages_path()):
            with codecs.open(res_name, 'r', 'utf-8') as file:
                text = file.read()

        else:
            text = sublime.load_binary_resource(res_name).decode("utf-8")

        return text.replace('\r\n', '\n').replace('\r', '\n')

    except OSError:
        log("Unable to load '%s'; resource not found" % res_name)

    except UnicodeError:
        print("Unable to decode '%s'; resource is not UTF-8" % res_name)

    return None


def current_help_package(view=None, window=None):
    """
    Obtain the package that contains the currently displayed help file or None
    if help is not visible.

    Looks in the help view provided, or the help view in the passed in window,
    or the help view in the currently active window.
    """
    view = view or find_help_view(window)
    return (view.settings().get("_hh_pkg") if view is not None else None)


def current_help_file(view=None, window=None):
    """
    Obtain the file that is currently being displayed in the help view or None
    if help is not visible.

    Looks in the help view provided, or the help view in the passed in window,
    or the help view in the currently active window.
    """
    view = view or find_help_view(window)
    return (view.settings().get("_hh_file") if view is not None else None)


def help_package_prompt(help_list, on_select, on_cancel=None):
    """
    Given a list of loaded help indexes, prompt the user to select one of the
    packages. on_select is invoked with the name of the selected package,
    while on_cancel is invoked if the user cancels the selection.
    """
    if not help_list:
        return log("No packages with help are installed", status=True)

    pkg_list = sorted([key for key in help_list])
    captions = [[help_list[key].package,
                 help_list[key].description]
        for key in pkg_list]

    def pick_package(index):
        package = None if index < 0 else captions[index][0]

        if index >= 0:
            return on_select(package) if on_select is not None else None

        return on_cancel() if on_cancel is not None else None

    sublime.active_window().show_quick_panel(
        captions,
        on_select=lambda index: pick_package(index))


###----------------------------------------------------------------------------
