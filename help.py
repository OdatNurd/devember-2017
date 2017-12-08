import sublime
import sublime_plugin

from .view import find_help_view, update_help_view
from .common import log, hh_syntax

###----------------------------------------------------------------------------


def _resource_for_help(pkg_info, help_file):
    """
    Get the resource name that references the help file in the given help
    package. The help file should be relative to the document root of the
    package.
    """
    return "%s/%s" % (pkg_info.doc_root, help_file)


def _load_help_file(pkg_info, help_file):
    """
    Load the contents of a help file contained in the provided help package.
    The help file should be relative to the document root of the package.

    Returns None if the help file cannot be loaded.
    """
    try:
        return sublime.load_resource(_resource_for_help(pkg_info, help_file))
    except:
        pass

    return None


def _display_help_file(pkg_info, help_file):
    """
    Load and display the help file contained in the provided help package. The
    help file should be relative to the document root of the package.

    The help will be displayed in the help view of the current window, which
    will be created if it does not exist.

    Does nothing if the help view is already displaying this file.

    Returns None if the help file could not be found/loaded or the help view
    on success.
    """
    view = find_help_view()
    window = view.window() if view is not None else sublime.active_window()

    if view is not None:
        window.focus_view(view)

        current_pkg = view.settings().get("_hh_pkg")
        current_file = view.settings().get("_hh_file")

        if help_file == current_file and pkg_info.package == current_pkg:
            return view

    help_text = _load_help_file(pkg_info, help_file)
    if help_text is not None:
        view = update_help_view(help_text, pkg_info.package, help_file,
                                hh_syntax("HyperHelp.sublime-syntax"))

        _post_process_links(view)
        _post_process_anchors(view)

        return view

    return log("Unable to find help file '%s'", help_file, status=True)


def _reload_help_file(help_list, help_view):
    """
    Reload the help file currently being displayed in the given view to pick
    up changes made since it was displayed. The information on the package and
    help file should be contained in the provided help list.

    Returns True if the file was reloaded successfully or False if not.
    """
    if help_view is None:
        log("No help topic is visible; cannot reload")
        return False

    settings = help_view.settings()
    package = settings.get("_hh_pkg", None)
    file = settings.get("_hh_file", None)
    pkg_info = help_list.get(package, None)

    if pkg_info is not None and file is not None:
        # Remove the file setting so the view will reload; put it back if the
        # reload fails so we can still track what the file used to be.
        help_view.settings().set("_hh_file", "")
        if _display_help_file(pkg_info, file) is None:
            help_view.settings().set("_hh_file", file)
            return false

        return True

    log("Unable to reload the current help topic")
    return False

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
