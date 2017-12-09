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

    def on_text_command(self, view, command, args):
        """
        Listen for the drag_select command with arguments that tell us that the
        user double clicked, see if they're double clicking on a link so we
        know if we should try to follow it or not.
        """
        if command == "drag_select" and args.get("by", None) == "words":
            event = args["event"]
            point = view.window_to_text((event["x"], event["y"]))

            if view.match_selector(point, "text.hyperhelp meta.link"):
                view.run_command("hyperhelp_navigate", {"nav": "follow_link"})
                return ("noop")

        return None


###----------------------------------------------------------------------------
