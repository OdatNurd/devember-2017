import sublime
import sublime_plugin


###----------------------------------------------------------------------------


class HyperHelpEventListener(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        """
        Provide custom key binding contexts for binding keys in hyperhelp
        views.
        """
        if key == "hyperhelp.is_authoring":
            lhs = view.is_read_only() == False
            rhs = bool(operand)
        else:
            return None

        if operator == sublime.OP_EQUAL:
            return lhs == rhs
        elif operator == sublime.OP_NOT_EQUAL:
            return lhs != rhs

        return None


###----------------------------------------------------------------------------
