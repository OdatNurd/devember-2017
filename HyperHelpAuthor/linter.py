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


# Linters produce an array of these tuples to indicate problems found in files.
# type can be one of "info", "warning" or "error".
LintResult = namedtuple("LintResult", [
    "type", "file", "line", "column", "message"
])


###----------------------------------------------------------------------------


class LinterBase():
    """
    The base class for all lint operations in the help linter.
    """
    def __init__(self, pkg_info):
        self.pkg_info = pkg_info
        self.issues = list()

    def lint(self, view, file_name):
        """
        This is invoked with a view that contains raw help text from the help
        file, which is contained in the help index given in the constructor.

        This will be invoked for each file to be linted.
        """
        pass

    def add(self, view, type, file, point, msg, *args):
        """
        Add a result to the internal result list. point is the location that
        is the focus of the error.
        """
        pos = view.rowcol(point)
        msg = msg % args
        self.issues.append(LintResult(type, file, pos[0] + 1, pos[1]+1, msg))

    def results(self):
        """
        This is invoked after all calls to the lint() method have finished to
        collect the final results of the lint operation.

        This should return a list of LintResult tuples that indicate the issues
        that have been found or an empty list if there are no issues.

        The default is to return the results instance variable.
        """
        return self.issues


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


def _format_lint(pkg_info, issues):
    """
    Takes a list of LintResult issues for a package and returns back output
    suitable for passing to _display_lint().
    """
    files = OrderedDict()
    for issue in issues:
        if issue.file not in files:
            files[issue.file] = []
        files[issue.file].append(issue)

    output = ["Linting in help package: %s\n" % pkg_info.package]

    warn = 0
    err = 0
    for file in files:
        output.append("%s:" % file)

        for issue in files[file]:
            output.append("    %s %d:%d %s" % (
                issue.type, issue.line, issue.column, issue.message))

            if issue.type == "warn":
                warn += 1
            elif issue.type == "err":
                err += 1

        output.append("")

    output.append("%d warnings, %d errors" % (warn, err))
    return output


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
    settings.set("result_file_regex", r"^([^:]+):$")
    settings.set("result_line_regex", r"^\D+(\d+):(\d+) (.*)")

    view.set_read_only(False)
    view.run_command("select_all")
    view.run_command("delete_left")
    view.run_command("append", {"characters": output})
    view.set_read_only(True)

    window.run_command("show_panel", {"panel": "output.HyperHelpAuthor Lint"})


###----------------------------------------------------------------------------


class MissingLinkAnchorLinter(LinterBase):
    """
    Lint one or more help files to find all links that are currently broken
    because their targets are not known.
    """
    def lint(self, view, file_name):
        topics = self.pkg_info.help_topics

        regions = view.find_by_selector("meta.link, meta.anchor")
        for pos in regions:
            link = view.substr(pos)
            if lookup_help_topic(self.pkg_info, link) is not None:
                continue

            stub = "link references unknown anchor '%s'"
            if view.match_selector(pos.begin(), "meta.anchor"):
                stub = "anchor '%s' is not in the help index"

            self.add(view, "warn", file_name, pos.begin(),
                     stub % link.replace("\t", " "))


###----------------------------------------------------------------------------


class HyperhelpAuthorLint(sublime_plugin.WindowCommand):
    def run(self):
        target = _find_lint_target(self.window.active_view())

        linters = []
        linters.append(MissingLinkAnchorLinter(target.pkg_info))

        spp = sublime.packages_path()
        doc_root = target.pkg_info.doc_root

        for file in target.files:
            view = _get_lint_file(os.path.join(spp, doc_root, file))
            if view is not None:
                for linter in linters:
                    linter.lint(view, file)

            else:
                log("Unable to lint '%s' in '%s'", file, pkg_info.package)

        issues = list()
        for linter in linters:
            issues += linter.results()

        _display_lint(self.window, target.pkg_info,
                      _format_lint(target.pkg_info, issues))

    def is_enabled(self):
        return _can_lint_view(self.window.active_view())


###----------------------------------------------------------------------------
