from argparse import ArgumentParser, Namespace
from collections.abc import Mapping
from io import StringIO
from os import putenv
from re import M, Pattern, compile
from sys import stderr, version_info
from typing import Any, NamedTuple, TypeGuard, cast

from IPython.core.display import display_html
from numpy import floor, prod, uint
from pandas import DataFrame, Index, Series, read_csv


def is_ipython() -> bool:
    try:
        get_ipython().__class__.__name__
        return True
    except NameError:
        return False

factorDict: Mapping[str, uint] = dict([('B', uint(1)),
                                       ('KB', uint(1024)),
                                       ('MB', uint(1048576)),
                                       ('GB', uint(1073741824))])


class Factor(NamedTuple):
    B: uint
    KB: uint
    MB: uint
    GB: uint


namedtup = Factor(**factorDict)

if version_info.major == 3 and version_info.minor < 10:
    print("This script uses features introduced in Python 3.10. Please upgrade your distribution.", file=stderr)  # noqa: E501
    raise EnvironmentError()


def unitreduce(byte: uint, factordex=(len(namedtup)-1)) -> tuple[uint, str]:
    if byte != 0:
        test = byte // namedtup[factordex]
        if test == 0.0:
            return unitreduce(byte, factordex - 1)
        else:
            return (test, namedtup._fields[factordex])
    else:
        return (byte, "B")


def is_list_2_str_tup(var: list[tuple[str | Any, ...]]) -> TypeGuard[list[tuple[str, str]]]:  # noqa: E501
    return all([isinstance(ob[0], str) and isinstance(ob[1], str)
                and len(ob) == 2 for ob in var])


def splitpath(dwalk: str) -> list[tuple[str, str]]:
    pattern: Pattern = compile(r'(/nfs/turbo/.+)$', M)
    with open(dwalk, 'rt') as file:
        stage = [tuple(pattern.split(line)[0:2]) for
                 line in file]
    assert is_list_2_str_tup(stage)
    return stage


def parse(dwalk: str):
    splitlist = splitpath(dwalk)
    mem_csv = StringIO()
    mem_csv.writelines([tup[0] + '\n' for tup in splitlist])
    mem_csv.seek(0)
    dataframe: DataFrame = read_csv(mem_csv, sep=' ',
                                    skipinitialspace=True, header=None,
                                    engine='c')
    pathseries = Series([tup[1] for tup in splitlist], name="Path", copy=True)
    cdf = dataframe.merge(right=pathseries, how="outer",
                          left_index=True, right_index=True)
    cdf[4] = cdf[4].map(factorDict)
    cdf = cdf.iloc[:, [1, 3, 4, 10]]
    cdf[3] = cdf.loc[:, [3, 4]].apply(prod, axis=1,  # type: ignore
                                      raw=True,
                                      result_type='expand',
                                      dtype=uint)
    cdf.drop(4, axis=1, inplace=True)
    cdf.columns = cast(Index, ('user', 'bytes', 'path'))
    groups = cdf.groupby('user', as_index=False)
    return groups


def top(args: Namespace) -> None:
    datatable: DataFrame = parse(args.file)
    selected = datatable.get_group(args.user)
    sorted = selected.sort_values('bytes', ascending=False)
    sorted['bytes'] = [str(int(num)) + un for num, un in
                       [unitreduce(x) for x in sorted['bytes'].to_list()]]
    styler = sorted.style
    if is_ipython():
        display_html(styler)
    else:
        with open('table.html', 'w') as output:
            styler.to_html(output, doctype_html=True)


def graph(args: Namespace) -> None:
    datatable: DataFrame = parse(args.file).sum()
    putenv("MPLBACKEND", "Cairo")
    total: uint = floor(datatable['bytes'].sum())
    percentlist = datatable['bytes'] / total * 100  # type: ignore
    percentlist = percentlist.transform(floor)
    percentlist.name = "perc"
    datatable = datatable.join(percentlist)
    datatable.drop(datatable.loc[datatable['perc'] == 0].index,  # type: ignore
                   inplace=True)
    ax = datatable.plot(kind="pie", x='user',
                        y='bytes', labels=datatable['user'],
                        legend=False, autopct='%.2f%%')
    ax.set_aspect('equal')
    ax.figure.savefig('./usage.png')


prsr: ArgumentParser = ArgumentParser()
prsr.add_argument("file", help="Text output of DWalk, sorted by user",
                  type=str)
prsr.add_argument('-j', default=1, type=int, required=False, metavar="threads")
subparsers = prsr.add_subparsers()
graphprsr: ArgumentParser = subparsers.add_parser("graph",
                                                  help="compare usage by user")
graphprsr.set_defaults(func=graph)
tblprsr: ArgumentParser = subparsers.add_parser("top",
                                                help="get largest directories for user")  # noqa: E501
tblprsr.add_argument("user", help="a unix user")
tblprsr.set_defaults(func=top)
args: Namespace = prsr.parse_args()
args.func(args)
