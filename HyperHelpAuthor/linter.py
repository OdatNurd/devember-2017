import sublime
import sublime_plugin

import os
from collections import OrderedDict, namedtuple

from hyperhelp.common import log, hh_syntax
from hyperhelp.core import help_index_list, lookup_help_topic


###----------------------------------------------------------------------------


# A representation of what is going to be linted.
LintTarget = namedtuple("LintTarget", [
    "target_type", "pkg_info", "files"
])


###----------------------------------------------------------------------------


def _can_lint_view(view):
    """
    Determine if the provided view can be the source of a lint. To be valid
    the view must represent a hyperhelp data file that has a path rooted in the
    Packages folder inside of a package whose help index is known.
    """
    if (view is not None and view.file_name() is not None and
            view.file_name().startswith(sublime.packages_path()) and
            view.match_selector(0, "text.hyperhelp")):

        name = os.path.relpath(view.file_name(), sublime.packages_path())
        pkg_name = name[:name.index(os.sep)]
        return pkg_name in help_index_list()

    return False


def _find_lint_target(view):
    """
    Examine a given view and return a LintTarget that describes what is being
    linted. None is returned if the view is not a valid lint target.
    """
    if not _can_lint_view(view):
        return None

    name = view.file_name()
    parts = os.path.relpath(name, sublime.packages_path()).split(os.sep)

    pkg_name = parts[0]
    target = parts[-1]

    pkg_info = help_index_list().get(pkg_name)

    if view.match_selector(0, "text.hyperhelp.help"):
        return LintTarget("single", pkg_info, [target])

    return LintTarget("package", pkg_info, list(pkg_info.help_files))


def _get_lint_file(filename):
    """
    Return a view that that contains the contents of the provided file name.
    If the file is not aready loaded, it is loaded into a hidden view and that
    is returned instead.

    Can return None if the file is not open and cannot be loaded.
    """
    for window in sublime.windows():
        view = window.find_open_file(filename)
        if view is not None:
            return view

    content = None
    try:
        with open(filename, 'r') as file:
            content = file.read()
    except:
        pass

    if content:
        view = sublime.active_window().create_output_panel("_hha_tmp", True)
        view.run_command("select_all")
        view.run_command("left_delete")
        view.run_command("append", {"characters": content})
        view.assign_syntax(hh_syntax("HyperHelp.sublime-syntax"))
        return view

    return None


def _display_lint(window, pkg_info, output):
    """
    Display the lint output provided into the given window. The output is
    assumed to have been generated from the provided package, which is used to
    know where the help files are located.
    """
    view = window.create_output_panel("HyperHelpAuthor Lint", False)
    basedir = os.path.join(sublime.packages_path(), pkg_info.doc_root)

    if not isinstance(output, str):
        output = "\n".join(output)

    settings = view.settings()
    settings.set("result_base_dir", basedir)
    settings.set("result_file_regex", r"^\s+([^:]+):(\d+):(\d+): (.*)$")

    view.set_read_only(False)
    view.run_command("select_all")
    view.run_command("delete_left")
    view.run_command("append", {"characters": output})
    view.set_read_only(True)

    window.run_command("show_panel", {"panel": "output.HyperHelpAuthor Lint"})


###----------------------------------------------------------------------------


class HyperhelpAuthorLint(sublime_plugin.WindowCommand):
    def run(self):
        lint = _find_lint_target(self.window.active_view())
        output = ["Linting package: %s\n" % lint.pkg_info.package]

        for file in lint.files:
            self.lint_file(lint.pkg_info, file, output)

        _display_lint(self.window, lint.pkg_info, output)

    def is_enabled(self):
        return _can_lint_view(self.window.active_view())

    def lint_file(self, pkg_info, target, output):
        name = os.path.join(sublime.packages_path(), pkg_info.doc_root, target)
        view = _get_lint_file(name)
        if view is None:
            return log("Unable to lint '%s' in '%s'", target, pkg_info.package,
                       status=True)

        output.append("%s:" % target)

        topics = pkg_info.help_topics
        result = OrderedDict()

        regions = view.find_by_selector("meta.link")
        for pos in regions:
            link = view.substr(pos)
            if lookup_help_topic(pkg_info, link) is not None:
                continue

            if link not in result:
                result[link] = list()

            result[link].append(view.rowcol(pos.begin()))

        count = len(result)
        if count == 0:
            return output.append("    No problems detected\n")

        for link in result.keys():
            display_link = link.replace("\t", " ")
            locs = result[link]
            for loc in locs:
                output.append("    %s:%d:%d: could not find '%s'" % (
                    target, loc[0] + 1, loc[1] + 1, display_link, ))

        output.append("")
        output.append("    %d anchor%s not in the help index" % (
            count, "" if count == 1 else "s"))
        output.append("")


###----------------------------------------------------------------------------
