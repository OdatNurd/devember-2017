import sublime

import textwrap


###----------------------------------------------------------------------------


def plugin_loaded():
    hha_setting.obj = sublime.load_settings("HyperHelpAuthor.sublime-settings")
    hha_setting.default = {
        "update_header_on_save": True,
    }


###----------------------------------------------------------------------------


def hha_setting(key):
    """
    Get a HyperHelpAuthor setting from a cached settings object.
    """
    default = hha_setting.default.get(key, None)
    return hha_setting.obj.get(key, default)


def is_authoring_source(view):
    """
    Given a view object, tells you if that view represents a help source file.
    """
    if view.match_selector(0, "text.hyperhelp.help"):
        return not view.is_read_only()

    return False


def format_template(template):
    """
    Given incoming text, remove all common indent, then strip away the leading
    and trailing whitespace from it.

    This is a modified version of code from Default/new_templates.py from the
    core Sublime code.
    """
    return textwrap.dedent(template).strip()


###----------------------------------------------------------------------------
