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

        self.index_file = os.path.relpath(
                              pkg_info.index_file,
                              "Packages/%s/" % (self.pkg_info.doc_root))

    def lint(self, view, file_name):
        """
        This is invoked with a view that contains raw help text from the help
        file, which is contained in the help index given in the constructor.

        This will be invoked for each file to be linted.
        """
        pass

    def add(self, view, m_type, file, point, msg, *args):
        """
        Add a result to the internal result list. point is the location that is
        the focus of the error. If view is None, the point is ignored and the
        issue is added at line 1, column 1.
        """
        pos = view.rowcol(point) if view is not None else (0, 0)
        msg = msg % args
        self.issues.append(LintResult(m_type, file, pos[0] + 1, pos[1]+1, msg))

    def add_index(self, m_type, msg, *args):
        """
        Add a result that is focused on the help index. As there is no way to
        know the proper location except by hand parsing the index, no view is
        needed and the position of the issue is always row 1, column 1.
        """
        return self.add(None, m_type, self.index_file, 0, msg, *args)

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


def can_lint_view(view):
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


def find_lint_target(view):
    """
    Examine a given view and return a LintTarget that describes what is being
    linted. None is returned if the view is not a valid lint target.
    """
    if not can_lint_view(view):
        return None

    name = view.file_name()
    parts = os.path.relpath(name, sublime.packages_path()).split(os.sep)

    pkg_name = parts[0]
    target = parts[-1]

    pkg_info = help_index_list().get(pkg_name)

    if view.match_selector(0, "text.hyperhelp.help"):
        return LintTarget("single", pkg_info, [target])

    return LintTarget("package", pkg_info, list(pkg_info.help_files))


def get_linters(target):
    """
    Given a LintTarget, return back an array of all of the linters that should
    be run for that target.

    Some targets may only be run on the package as a whole while others may be
    allowed on a file by file basis. The returned linters may also be affected
    by user settings.
    """
    linters = []
    linters.append(MissingLinkAnchorLinter(target.pkg_info))

    if target.target_type == "package":
        linters.append(MissingHelpSourceLinter(target.pkg_info))

    return linters


def get_lint_file(filename):
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


def format_lint(pkg_info, issues, window=None):
    """
    Takes a list of LintResult issues for a package and returns back output
    suitable for passing to display_lint().

    If a window is provided, display_lint() is called prior to returning in
    order to display the output first.
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
            issue_pos = "%d:%d" % (issue.line, issue.column)
            output.append("    %-7s @ %-7s %s" % (
                issue.type, issue_pos, issue.message))

            if issue.type == "warning":
                warn += 1
            elif issue.type == "error":
                err += 1

        output.append("")

    output.append("%d warning%s, %d error%s" % (
        warn,
        "" if warn == 1 else "s",
        err,
        "" if err == 1 else "s"))

    if window:
        display_lint(window, pkg_info, output)

    return output


def display_lint(window, pkg_info, output):
    """
    Display the lint output provided into the given window. The output is
    assumed to have been generated from the provided package, which is used to
    know where the help files are located.
    """
    view = window.create_output_panel("HyperHelpAuthor Lint", False)
    basedir = os.path.join(sublime.packages_path(), pkg_info.doc_root)

    if not isinstance(output, str):
        output = "\n".join(output)

    view.assign_syntax(hh_syntax("HyperHelpLinter.sublime-syntax"))

    settings = view.settings()
    settings.set("result_base_dir", basedir)
    settings.set("result_file_regex", r"^([^:]+):$")
    settings.set("result_line_regex", r"^.*?@ (\d+):(\d+)\s+(.*)$")

    view.set_read_only(False)
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

            self.add(view, "warning", file_name, pos.begin(),
                     stub % link.replace("\t", " "))


class MissingHelpSourceLinter(LinterBase):
    """
    Lint the help index to determine if the list of help files listed in the
    index matches the list of help files that exist for the package.
    """
    def __init__(self, pkg_info):
        super().__init__(pkg_info)

        root = "Packages/%s/" % (self.pkg_info.doc_root)
        d_files = {file[len(root):] for file in sublime.find_resources("*.txt")
                      if file.startswith(root)}

        i_files = {key for key in self.pkg_info.help_files.keys()}

        for file in d_files - i_files:
            self.add_index(
                "warning",
                "Help file '%s' is in Packages/%s/ but missing from the index",
                file, self.pkg_info.doc_root)

        for file in i_files - d_files:
            self.add_index(
                "error",
                "Help file '%s' is in the index but not in Packages/%s/",
                file, self.pkg_info.doc_root)


###----------------------------------------------------------------------------
