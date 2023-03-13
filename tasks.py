from invoke import task


@task
def run(c):
    c.run("poetry run gradio run.py")
