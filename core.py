import sublime

from .common import log, hh_syntax
from .view import find_help_view, update_help_view

from .help import _post_process_links, _post_process_anchors

###----------------------------------------------------------------------------


def display_help(help_res):
    """
    Display the provided help resource in the help view, creating it if needed.
    If the view is already displaying this resource, the view is focused but
    nothing else happens.

    The help view is returned back, unless the help file could not be loaded.
    """
    parts = help_res.split("/")
    if len(parts) < 3:
        return log("Unable to load help file", status=True)

    help_pkg = parts[1]
    help_file = parts[-1]

    view = find_help_view()
    window = view.window() if view is not None else sublime.active_window()

    if view is not None:
        window.focus_view(view)

        current_pkg = view.settings().get("_hh_pkg")
        current_file = view.settings().get("_hh_file")

        if help_file == current_file and help_pkg == current_pkg:
            return view

    try:
        help_txt = sublime.load_resource(help_res)
    except:
        return log("Unable to load help file '%s'" % help_file, status=True)

    view = update_help_view(help_txt, help_pkg, help_file,
                            hh_syntax("HyperHelp.sublime-syntax"))
    _post_process_links(view)
    _post_process_anchors(view)


###----------------------------------------------------------------------------
