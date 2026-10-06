import nox

DJANGO_VERSIONS = ["4.2", "5.2", "6.0"]


@nox.session(python=["3.12", "3.13", "3.14"], venv_backend="uv")
@nox.parametrize("django", DJANGO_VERSIONS)
def tests(session, django):
    # Django 4.2 does not support Python 3.14
    if django == "4.2" and session.python == "3.14":
        session.skip("Django 4.2 does not support Python 3.14")

    session.install(f"django~={django}.0")
    session.install(".[polymorphic,workflow,ordered,test]")

    # One XML report per session: all sessions run from the repo root, so a shared
    # coverage.xml would be overwritten by each session in turn. See issue #105.
    xml_report = f"--cov-report=xml:coverage-py{session.python}-dj{django}.xml"
    session.run("pytest", "tests", "-n", "auto", "--cov", "--cov-report=term-missing", xml_report, *session.posargs)


@nox.session(python=["3.12", "3.13", "3.14"], venv_backend="uv")
@nox.parametrize("django", DJANGO_VERSIONS)
def examples(session, django):
    # Django 4.2 does not support Python 3.14
    if django == "4.2" and session.python == "3.14":
        session.skip("Django 4.2 does not support Python 3.14")

    session.install(f"django~={django}.0")
    session.install(".[all,test,examples]", "-r", "requirements/demo.txt")

    with session.chdir("./examples/bootstrap5"):
        session.run("pytest", *session.posargs)
