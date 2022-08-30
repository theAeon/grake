import click

from .usagebyuser import graphcmd, topcmd


@click.group()
@click.option('-j', '--threads', default=1, help="number of threads", metavar='threads', type=int)
@click.pass_context
def cli(ctx, threads):
    ctx.obj = {}
    ctx.obj['threads'] = threads


@cli.command()
@click.argument('filename', type=click.Path(exists=True), required=True)
@click.pass_context
def graph(ctx, filename):
    """compare usage by user"""
    graphcmd(ctx.obj['threads'], filename)


@cli.command()
@click.argument('filename', type=click.Path(exists=True), required=True)
@click.argument('user', nargs=1, required=True)
@click.pass_context
def top(ctx, filename, user):
    """get largest directories for user"""
    topcmd(ctx.obj['threads'], filename, user)
