import sublime

import textwrap


###----------------------------------------------------------------------------


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
