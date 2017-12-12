import sublime
import sublime_plugin

import os
import textwrap
import datetime

from .common import log, hh_syntax, current_help_package, help_package_prompt
from .core import help_index_list
from .core import reload_help_file


###----------------------------------------------------------------------------


def _reformat(template):
    """
    Reformat the passed in text to not be indented, so that we can easily
    inline strings. Swiped almost wholesale from Detaul/new_templates.py
    except that I don't like extra trailing newlines.
    """
    return textwrap.dedent(template).lstrip().rstrip()


###----------------------------------------------------------------------------


class HyperhelpAuthorCreateHelp(sublime_plugin.WindowCommand):
    """
    Create a new help file in the package provided. If no package is given and
    one cannot be inferred from the current help view, the user will be
    prompted to supply one. The prompt always occurs if the argument asks.
    """
    def run(self, package=None, prompt=False):
        package = package or current_help_package(window=self.window)
        if package is None or prompt:
            return help_package_prompt(help_index_list(),
                                       on_select=lambda pkg: self.run(pkg))

        self.window.show_input_panel("New Help File", "",
                                     lambda file: self.create_file(package, file),
                                     None, None)

    def create_file(self, package, file):
        if not file:
            return log("No help file given; skipping creation", status=True)

        pkg_info = help_index_list().get(package)
        local_path = os.path.join(sublime.packages_path(),
                                 pkg_info.doc_root,
                                 file)

        help_file = os.path.split(local_path)

        os.makedirs(help_file[0], exist_ok=True)

        view = self.window.new_file()
        view.settings().set("default_dir", help_file[0])
        view.set_name(help_file[1])
        view.assign_syntax(hh_syntax("HyperHelp.sublime-syntax"))

        template = _reformat(
            """
            %%hyperhelp title="${1:Title}" date="${2:%s}"

            $0
            """ % datetime.date.today().strftime("%Y-%m-%d"))

        view.run_command("insert_snippet", {"contents": template})


class HyperhelpAuthorReloadHelpCommand(sublime_plugin.TextCommand):
    """
    If the current view is a hyperhelp help view, this will reload the file
    currently being displayed in the view.
    """
    def run(self, edit):
        help_file = self.view.settings().get("_hh_file", None)
        if reload_help_file(help_index_list(), self.view):
            log("Reloaded help file '%s'", help_file, status=True)

    def is_enabled(self):
        settings = self.view.settings()
        return settings.has("_hh_pkg") and settings.has("_hh_file")


class HyperhelpAuthorReloadIndexCommand(sublime_plugin.TextCommand):
    """
    If the current view is a hyperhelp index view, this will attempt to reload
    the help index so that the current changes will immediately take effect.
    """
    def run(self, edit):
        filename = os.path.realpath(self.view.file_name())
        if not filename.startswith(sublime.packages_path()):
            return log("Cannot reload help index; not in package", status=True)

        filename = os.path.relpath(filename, sublime.packages_path())
        package = os.path.split(filename)[0].split(os.sep)[0]

        if package not in help_index_list():
            log("Package index for '%s' not previously loaded; reloading all indexes",
                package, status=True)
            package = None
        else:
            log("Reloading help index for package '%s'", package, status=True)

        help_index_list(reload=True, package=package)

    def is_enabled(self):
        return (self.view.match_selector(0, "text.hyperhelp.index") and
                self.view.file_name() is not None)


###----------------------------------------------------------------------------