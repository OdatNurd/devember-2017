import sublime

from .common import log, hh_syntax
from .view import find_help_view, update_help_view, focus_on

from .help_index import _load_help_index, _scan_help_packages
from .help import _post_process_links, _resource_for_help
from .help import _load_help_file, _display_help_file, _reload_help_file


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


###----------------------------------------------------------------------------


def load_help_index(index_resource):
    """
    Given an index resource that points to a hyperhelp.json file, load the help
    index and return back a normalized version. Returns None on error.
    """
    return _load_help_index(index_resource)


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

        result = _load_help_index(pkg_info.index_file)
        if result is not None:
            help_list[result.package] = result

    return help_list


def help_file_resource(pkg_info, help_file):
    """
    Get the resource name that references the help file in the given help
    package. The help file should be relative to the document root of the
    package.
    """
    return _resource_for_help(pkg_info, help_file)


def load_help_file(pkg_info, help_file):
    """
    Load the contents of a help file contained in the provided help package.
    The help file should be relative to the document root of the package.

    Returns None if the help file cannot be loaded.
    """
    return _load_help_file(pkg_info, help_file)


def display_help_file(pkg_info, help_file):
    """
    Load and display the help file contained in the provided help package. The
    heop file should be relative to the document root of the package.

    The help will be displayed in the help view of the current window, which
    will be created if it does not exist.

    Does nothing if the help view is already displaying this file.

    Returns None if the help file could not be found/loaded or the help view
    on success.
    """
    return _display_help_file(pkg_info, help_file)


def reload_help_file(help_list, help_view):
    """
    Reload the help file currently being displayed in the given view to pick
    up changes made since it was displayed. The information on the package and
    help file should be contained in the provided help list.

    Returns True if the file was reloaded successfully or False if not.
    """
    return _reload_help_file(help_list, help_view)


def show_help_topic(package, topic):
    """
    Attempt to display the help for the provided topic in the given package
    (both strings). This will transparently create a new help view if needed, as
    well as loading the appropriate help file before jumping to the topic.

    The return value is True if the topic was displayed or False otherwise.
    """
    pkg_info = help_index_list().get(package, None)
    if pkg_info is None:
        return False

    inner_topic = topic.replace(" ", "\t").casefold()
    help_file = pkg_info.help_topics.get(inner_topic, {}).get("file", None)
    if help_file is None:
        log("Unknown help topic '%s", topic, status=True)
        return False

    help_view = display_help_file(pkg_info, help_file)
    if help_view is None:
        log("Unable to load help file '%s'", help_file, status=True)
        return False

    anchors = help_view.settings().get("_hh_nav", [])
    for anchor in anchors:
        if inner_topic == anchor[0].casefold():
            focus_on(help_view, anchor[1], at_center=True)
            return True

    log("Unable to find topic '%s' in help file '%s'", topic, help_file)


###----------------------------------------------------------------------------
