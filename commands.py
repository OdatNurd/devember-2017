import sublime
import sublime_plugin

import os

from .common import log, current_help_package, help_package_prompt
from .view import focus_on
from .core import help_index_list
from .core import show_help_topic


###----------------------------------------------------------------------------


class HyperhelpTopicCommand(sublime_plugin.ApplicationCommand):
    """
    Display the provided help topic inside the given package. If package is
    None, infer it from the currently active help view.
    """
    def run(self, package=None, topic="index.txt"):
        package = package or current_help_package()
        topic = topic or "index.txt"

        if package is None:
            return log("Cannot display topic '%s'; cannot determine package",
                topic, status=True)

        show_help_topic(package, topic)


class HyperhelpContentsCommand(sublime_plugin.ApplicationCommand):
    """
    Display the table of contents for the package provided. If no package is
    given and one cannot be inferred from the current help view, the user will
    be prompted to supply one. The prompt always occurs if the argument asks.
    """
    def run(self, package=None, prompt=False):
        package = package or current_help_package()
        if package is None or prompt:
            return help_package_prompt(help_index_list(),
                                       on_select=lambda pkg: self.run(pkg))

        pkg_info = help_index_list().get(package, None)
        if pkg_info is None:
            return log("Cannot display table of contents; unknown package '%s",
                       package, status=True)

        self.show_toc(pkg_info, pkg_info.help_toc, [])

    def is_enabled(self, package=None, prompt=False):
        if prompt == False:
            package = package or current_help_package()
            if package is None:
                return False

        return True

    def show_toc(self, pkg_info, items, stack):
        captions = [[item["caption"], item["topic"].replace("\t", " ") +
            (" ({} topics)".format(len(item["children"])) if "children" in item else "")]
            for item in items]

        if not captions and not stack:
            return log("No help topics defined for package '%s'",
                       pkg_info.package, status=True)

        if stack:
            captions.insert(0, ["..", "Go back"])

        sublime.active_window().show_quick_panel(
            captions,
            on_select=lambda index: self.select(pkg_info, items, stack, index))

    def select(self, pkg_info, items, stack, index):
        if index >= 0:
            # When the stack isn't empty, the first item takes us back.
            if index == 0 and len(stack) > 0:
                items = stack.pop()
                return self.show_toc(pkg_info, items, stack)

            # Compenstate for the "go back" item when the stack's not empty
            if len(stack) > 0:
                index -= 1

            entry = items[index]
            children = entry.get("children", None)

            if children is not None:
                stack.append(items)
                return self.show_toc(pkg_info, children, stack)

            show_help_topic(pkg_info.package, entry["topic"])


class HyperhelpIndexCommand(sublime_plugin.ApplicationCommand):
    """
    Display the index for the package provided. If no package is given and one
    cannot be inferred from the current help view, the user will be prompted to
    supply one. The prompt always occurs if the argument asks.
    """
    def run(self, package=None, prompt=False):
        package = package or current_help_package()
        if package is None or prompt:
            return help_package_prompt(help_index_list(),
                                       on_select=lambda pkg: self.run(pkg))

        pkg_info = help_index_list().get(package, None)
        if pkg_info is None:
            return log("Cannot display topic index; unknown package '%s",
                       package, status=True)

        topics = [pkg_info.help_topics.get(topic)
                  for topic in sorted(pkg_info.help_topics.keys())]

        items = [[t["caption"], t["topic"].replace("\t", " ")]
                 for t in topics]

        if not items:
            return log("No help topics defined for package '%s'",
                       package, status=True)

        sublime.active_window().show_quick_panel(
            items,
            on_select=lambda index: self.select(pkg_info, items, index))

    def is_enabled(self, package=None, prompt=False):
        if prompt == False:
            package = package or current_help_package()
            if package is None:
                return False

        return True

    def select(self, pkg_info, items, index):
        if index >= 0:
            show_help_topic(pkg_info.package, items[index][1])


class HyperhelpNavigateCommand(sublime_plugin.TextCommand):
    """
    Perform navigation from within a help file
    """
    available_nav = ["find_anchor", "follow_link"]

    def run(self, edit, nav, prev=False):
        if nav == "find_anchor":
            return self.anchor_nav(prev)

        return self.follow_link()

    def is_enabled(self, nav, prev=False):
        settings = self.view.settings()
        return (nav in self.available_nav and
                settings.has("_hh_pkg") and settings.has("_hh_file"))

    def anchor_nav(self, prev):
        anchors = self.view.settings().get("_hh_nav")
        if not anchors:
            return

        point = self.view.sel()[0].begin()
        fallback = anchors[-1] if prev else anchors[0]

        pick = lambda p: (point < p[1][0]) if not prev else (point > p[1][0])
        for pos in reversed(anchors) if prev else anchors:
            if pick(pos):
                return focus_on(self.view, pos[1])

        focus_on(self.view, fallback[1])

    def follow_link(self):
        point = self.view.sel()[0].begin()
        if self.view.match_selector(point, "text.hyperhelp meta.link"):
            topic = self.view.substr(self.view.extract_scope(point))

            package = self.view.settings().get("_hh_pkg")
            show_help_topic(package, topic)


###----------------------------------------------------------------------------
