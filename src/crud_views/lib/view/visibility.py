def cv_resolve_action(ctx: dict | None) -> dict | None:
    """Resolve an action's button data to show / disable / hide (#149).

    An action is usable when the user may access its target (cv_access is True) and the action is
    enabled (cv_action_enabled is not False). An unusable action is hidden unless its target view
    resolved cv_inaccessible_actions to "disable" (see CrudView.cv_get_inaccessible_actions).

    Returns None to hide, a copy flagged cv_disabled=True (cv_url=None, cv_disabled_reason
    "permission" | "state") to render disabled, or a copy flagged cv_disabled=False to render
    normally. Never mutates ctx; resolving resolved data again gives the same result.
    """
    if not ctx:
        return None
    usable = ctx.get("cv_access") is True and ctx.get("cv_action_enabled") is not False
    if usable:
        return {**ctx, "cv_disabled": False}
    if ctx.get("cv_inaccessible_actions") != "disable":
        return None
    reason = "permission" if ctx.get("cv_access") is not True else "state"
    return {**ctx, "cv_disabled": True, "cv_url": None, "cv_disabled_reason": reason}
