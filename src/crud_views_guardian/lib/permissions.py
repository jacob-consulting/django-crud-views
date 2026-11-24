"""Private Guardian grant reuse for the lifetime of the supplied user object."""


def _get_guardian_checker(user):
    checker = getattr(user, "_cv_guardian_checker", None)
    if checker is None:
        from guardian.core import ObjectPermissionChecker

        checker = ObjectPermissionChecker(user)
        setattr(user, "_cv_guardian_checker", checker)
    return checker
