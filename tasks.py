from invoke import task
from pathlib import Path


@task
def populate(c):
    if not Path("lite.db").is_file():
        c.run("poetry run python populate_db.py")
    else:
        print(">> DB already populated")


@task(populate)
def run(c):
    print(">> Launching webui")
    c.run("poetry run gradio run.py")
