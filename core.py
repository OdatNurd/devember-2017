import sublime

from .common import log, hh_syntax
from .view import find_help_view, update_help_view

from .help_index import _load_help_index, _scan_help_packages
from .help import _post_process_links, _post_process_anchors


###----------------------------------------------------------------------------


def help_index_list(reload=False, package=None):
    """
    Obtain or reload the help index information for all packages. This demand
    loads the indexes on first access and can optionally reload all package
    indexes or only a single one, as desired.
    """
    initial_load = False
    if not hasattr(help_index_list, "index"):
        initial_load = True
        help_index_list.index = _scan_help_packages()

    if reload and not initial_load:
        help_index_list.index = reload_help_index(help_index_list.index, package)

    return help_index_list.index


def reload_help_index(help_list, package):
    """
    Reload the help index for the provided package from within the given help
    list, updating the help list to record the new data.

    If no package name is provided, the help list provided is ignored and all
    help indexes are reloaded and returned in a new help list.

    Attempts to reload a package that is not in the given help list has no
    effect.
    """
    if package is None:
        log("Recanning all help index files")
        return _scan_help_packages()

    pkg_info = help_list.get(package, None)
    if pkg_info is None:
        log("Package '%s' was not previously loaded; cannot reload", package)
    else:
        log("Reloading help index for package '%s'", package)

        result = _load_help_index(pkg_info.package, pkg_info.index_file)
        if result is not None:
            help_list[result.package] = result

    return help_list


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
