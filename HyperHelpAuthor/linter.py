import sublime
import sublime_plugin

import os
from collections import OrderedDict

from hyperhelp.common import log, hh_syntax
from hyperhelp.core import help_index_list, lookup_help_topic


###----------------------------------------------------------------------------


class HyperhelpAuthorLint(sublime_plugin.WindowCommand):
    def run(self):
        pkg_info, targets = self.get_lint_targets()
        if pkg_info is None:
            return log("Unable to lint; package is not in help index",
                       status=True)

        output = []
        output.append("Linting Help Package: %s\n" % pkg_info.package)
        for target in targets:
            self.lint_target(pkg_info, target, output)

        self.display_output(pkg_info, output)

    def is_enabled(self):
        view = self.window.active_view()
        if (view.match_selector(0, "text.hyperhelp") and
                view.is_read_only() == False and
                view.file_name() is not None):
            return view.file_name().startswith(sublime.packages_path())

        return False

    def get_lint_targets(self):
        view = self.window.active_view()
        name = os.path.relpath(view.file_name(), sublime.packages_path())
        parts = name.split(os.sep)

        pkg_name = parts[0]
        target = parts[-1]

        pkg_info = help_index_list().get(pkg_name, None)
        if pkg_info is None:
            return (None, None)

        if view.match_selector(0, "text.hyperhelp.help"):
            return (pkg_info, [target])

        return (pkg_info, list(pkg_info.help_files))

    def get_temp_view(self, filename):
        content = None
        try:
            with open(filename, 'r') as file:
                content = file.read()
        except:
            pass

        if content:
            view = self.window.create_output_panel("_hh_tmp", True)
            view.run_command("select_all")
            view.run_command("left_delete")
            view.run_command("append", {"characters": content})
            view.assign_syntax(hh_syntax("HyperHelp.sublime-syntax"))
            return view

        return None

    def lint_target(self, pkg_info, target, output):
        name = os.path.join(sublime.packages_path(), pkg_info.doc_root, target)
        view = self.window.find_open_file(name)
        view = view or self.get_temp_view(name)
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


    def display_output(self, pkg_info, output):
        lint_view = self.window.create_output_panel("HyperHelp Lint", False)
        s = lint_view.settings()

        base = os.path.join(sublime.packages_path(), pkg_info.doc_root)
        s.set("result_base_dir", base)
        s.set("result_file_regex", r"^\s+([^:]+):(\d+):(\d+): (.*)$")

        lint_view.set_read_only(False)
        lint_view.run_command("select_all")
        lint_view.run_command("delete_left")
        lint_view.run_command("append", {"characters": "\n".join(output)})
        lint_view.set_read_only(True)

        self.window.run_command("show_panel", {"panel": "output.HyperHelp Lint"})

###----------------------------------------------------------------------------
