import click

from .usagebyuser import graphcmd, topcmd


@click.group()
@click.option('-j', '--threads', default=1, help="number of threads", metavar='threads', type=int)
@click.pass_context
def cli(ctx, thread):
    ctx.obj['thread'] = thread


@cli.command()
@click.argument('filename', type=click.Path(exists=True), help="Text output of DWalk, sorted by user", required=True)
@click.pass_context
def graph(ctx, file):
    """compare usage by user"""
    graphcmd(ctx.thread, file)


@cli.command()
@click.argument('filename', type=click.Path(exists=True), help="Text output of DWalk, sorted by user", required=True)
@click.argument('user', nargs=1, help="a unix user", required=True)
@click.pass_context
def top(ctx, file, user):
    """get largest directories for user"""
    topcmd(ctx.thread, file, user)
