import nox

DJANGO_VERSIONS = ["4.2", "5.2", "6.0"]


@nox.session(python=["3.12", "3.13", "3.14"], venv_backend='uv')
@nox.parametrize("django", DJANGO_VERSIONS)
def tests(session, django):
    # Django 4.2 does not support Python 3.14
    if django == "4.2" and session.python == "3.14":
        session.skip("Django 4.2 does not support Python 3.14")

    session.install(f"django~={django}.0")
    session.install(".[bootstrap5,polymorphic,test]")

    with session.chdir("./tests"):
        session.run("pytest", "--cov", "--cov-report=term-missing", *session.posargs)
