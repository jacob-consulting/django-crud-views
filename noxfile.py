import nox


@nox.session(python=["3.11", "3.12"], venv_backend='uv')
def tests(session):
    session.install(".[bootstrap5,test]")

    with session.chdir("./tests"):
        session.run("pytest")
