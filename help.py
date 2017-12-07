import sublime
import sublime_plugin

from .common import log, hh_syntax
from .view import find_help_view, update_help_view


###----------------------------------------------------------------------------


def plugin_loaded():
    """
    On plugin load, find all help views and make sure that their link text is
    underlined.
    """
    for window in sublime.windows():
        help_view = find_help_view(window)
        if help_view is not None:
            _post_process_links(help_view)


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


def _post_process_anchors(help_view):
    """
    Find all of the hidden anchors in the help view and remove the text that
    marks them as anchors, so they just appear as plain text. The position of
    these anchors is stored in a setting in the view for later retreival.
    """
    help_view.set_read_only(False)

    regions = help_view.find_by_selector("meta.anchor.hidden")
    anchors = []
    adj = 4 * (len(regions) - 1)
    for pos in reversed(regions):
        # Adjust the positions of all anchors relative to their position in
        # the document, since they all move backwards as we process them. Those
        # closer to the bottom of the document move more.
        anchor = help_view.substr(pos)
        adjusted_pos = sublime.Region(pos.a - adj - 2, pos.b - adj - 2)
        anchors.append([anchor, adjusted_pos])
        adj -= 4

        # Remove the marker
        help_view.sel().clear()
        help_view.sel().add(sublime.Region(pos.a - 2, pos.b + 2))
        help_view.run_command("insert", {"characters": anchor})

    # The full nav list is the list of hidden anchors plus the list of regular
    # anchors, sorted by position in the buffer. We need to convert regions to
    # arrays of points because regions are not iterable and can't be stored in
    # settings.
    regions = help_view.find_by_selector("meta.anchor")
    nav_list = ([[a[0], [a[1].a, a[1].b]] for a in reversed(anchors)] +
                [[help_view.substr(r), [r.a, r.b]] for r in regions])

    help_view.settings().set("_hh_nav", sorted(nav_list,
                                               key=lambda item: item[1][0]))

    help_view.set_read_only(True)


def _post_process_links(help_view):
    """
    Find all of the links in the provided help view and underline them.
    """
    regions = help_view.find_by_selector("meta.link")
    help_view.add_regions("_hh_links", regions, "storage",
        flags=sublime.DRAW_SOLID_UNDERLINE|sublime.DRAW_NO_FILL|sublime.DRAW_NO_OUTLINE)


###----------------------------------------------------------------------------
