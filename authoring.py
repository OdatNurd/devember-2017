import sublime
import sublime_plugin

import os
import datetime
import re

from .common import log, hh_syntax, current_help_package, help_package_prompt
from .authoring_common import format_template, is_authoring_source
from .authoring_common import local_help_filename, open_local_help
from .authoring_common import open_help_index, apply_authoring_settings
from .core import help_index_list
from .core import reload_help_file


###----------------------------------------------------------------------------


# Match a help header line focusing on the date field.
_header_date_re = re.compile(r'^(%hyperhelp.*\bdate=")(\d{4}-\d{2}-\d{2})(".*)')


###----------------------------------------------------------------------------


class HyperhelpAuthorUpdateHeader(sublime_plugin.TextCommand):
    """
    If the current file is a help file that contains a header with a last
    modified date field, this will update the date field to be the current
    date. Quiet controls if the status line shows status about this or not.
    """
    def run(self, edit, quiet=False):
        now = datetime.date.today().strftime("%Y-%m-%d")

        h_line = self.view.line(0)
        header = self.view.substr(h_line)

        msg = "Help file date header is already current"
        match = _header_date_re.match(header)
        if match and match.group(2) != now:
            header = match.expand(r'\g<1>%s\g<3>' % now)
            self.view.replace(edit, h_line, header)

            msg = "Help file date header updated to the most recent date"

        if not quiet:
            log(msg, status=True)


    def is_enabled(self, quiet=False):
        return is_authoring_source(self.view)


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

        if help_index_list().get(package, None) is None:
            return log("Cannot add help file; package '%s' unknown", package,
                       dialog=True)

        self.window.show_input_panel("New Help File (%s)" % package, "",
                                     lambda file: self.create_file(package, file),
                                     None, None)

    def create_file(self, package, file):
        if not file:
            return log("No help file given; skipping creation", status=True)

        pkg_info = help_index_list().get(package)
        local_path = local_help_filename(pkg_info, file)

        help_file = os.path.split(local_path)

        os.makedirs(help_file[0], exist_ok=True)

        view = self.window.new_file()
        view.settings().set("default_dir", help_file[0])
        view.set_name(help_file[1])
        apply_authoring_settings(view)

        template = format_template(
            """
            %%hyperhelp title="${1:Title}" date="${2:%s}"

            $0
            """ % datetime.date.today().strftime("%Y-%m-%d"))

        view.run_command("insert_snippet", {"contents": template})


class HyperhelpAuthorEditHelp(sublime_plugin.WindowCommand):
    """
    Open an existing help file from the package provided. If no package is
    given and one cannot be inferred from the current help view, the user will
    be prompted to supply one. The prompt always occurs if the argument asks.
    """
    def run(self, package=None, prompt=False):
        package = package or current_help_package(window=self.window)
        if package is None or prompt:
            return help_package_prompt(help_index_list(),
                                       on_select=lambda pkg: self.run(pkg))

        pkg_info = help_index_list().get(package, None)
        if pkg_info is None:
            return log("Cannot edit help file; package '%s' unknown", package,
                       dialog=True)

        files = pkg_info.help_files
        items = [[key, files[key]] for key in files]

        if not items:
            return log("The help index for '%s' lists no help files", package,
                       dialog=True )

        self.window.show_quick_panel(
            items=items,
            on_select=lambda i: self.edit_file(pkg_info, items, i))

    def edit_file(self, pkg_info, items, index):
        if index >= 0:
            open_local_help(pkg_info, items[index][0], window=self.window)


class HyperhelpAuthorEditIndex(sublime_plugin.WindowCommand):
    """
    Open the index for the help package provided. If no package is given and one
    cannot be inferred from the current help view, the user will be prompted to
    supply one. The prompt always occurs if the argument asks.
    """
    def run(self, package=None, prompt=False):
        package = package or current_help_package(window=self.window)
        if package is None or prompt:
            return help_package_prompt(help_index_list(),
                                       on_select=lambda pkg: self.run(pkg))

        pkg_info = help_index_list().get(package, None)
        if pkg_info is None:
            return log("Cannot edit help file; package '%s' unknown", package,
                       dialog=True)

        open_help_index(pkg_info)


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
