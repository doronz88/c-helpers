import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Optional

import click
from plumbum import ProcessExecutionError, local

clang = local['clang']

SUFFIX = '.mm' if os.uname().sysname == 'Darwin' else '.cpp'

HEADERS = ['stdio.h', 'unistd.h', 'errno.h', 'sys/socket.h', 'sys/stat.h', 'sys/types.h', 'sys/dir.h',
           'dlfcn.h', 'sys/utsname.h', 'resolv.h', ]

if os.uname().sysname == 'Darwin':
    HEADERS += ['sys/dirent.h', 'AppleArchive/AADefs.h', ]
else:
    HEADERS += ['dirent.h', ]

FRAMEWORKS = ['Foundation', 'CoreFoundation', 'SystemConfiguration', 'CoreGraphics', 'CoreImage']

C_STRUCT_MEMBER_FORMAT = r'''
int main()
{{
    {name} var;
    printf("{highlight}sizeof({name}): {default}%lu (0x%.2x)\n\
{highlight}offsetof({name}, {member}): {default}%lu (0x%.2x)\n\
{highlight}sizeof({name}::{member}): {default}%lu (0x%.2x)", \
sizeof(var), sizeof(var), __builtin_offsetof({name}, {member}), __builtin_offsetof({name}, {member}), \
sizeof(var.{member}), sizeof(var.{member}));

    return 0;
}}
'''

C_STRUCT_FORMAT = r'''
int main()
{{
    {name} var;
    printf("{highlight}sizeof({name}): {default}%lu (0x%.2x)", sizeof(var), sizeof(var));

    return 0;
}}
'''

C_CONST_FORMAT = r'''
int main()
{{
    printf("%lu (0x%.2x)", {name}, {name});

    return 0;
}}
'''

ERROR_DELIMITER = 'error: '


def build_and_execute(filename: Path) -> None:
    try:
        out_file = f'{filename}.out'
        clang(filename, '-o', out_file, '-fmodules', '-fcxx-modules')
        print(local[out_file]())
    except ProcessExecutionError as e:
        for line in e.stderr.splitlines():
            if ERROR_DELIMITER not in line:
                continue
            click.secho(line.split(ERROR_DELIMITER, 1)[1], fg='red')
            return


def get_frameworks_if_needed(additional_frameworks: List[str]) -> str:
    result = ''
    if os.uname().sysname == 'Darwin':
        for framework in FRAMEWORKS + additional_frameworks:
            result += f'@import {framework};\n'
    return result


def get_headers(additional_headers: List[str]) -> str:
    result = ''
    for header in HEADERS + additional_headers:
        result += f'#include <{header}>\n'
    return result


class BaseCommand(click.Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params[:0] = [
            click.Option(('headers', '-h', '--header'), multiple=True, help='additional header to include'),
            click.Option(('frameworks', '-f', '--framework'), multiple=True, help='additional framework to import'),
        ]


@click.command(cls=BaseCommand)
@click.argument('name')
@click.argument('member', required=False)
def c_struct(headers: List[str], frameworks: List[str], name: str, member: Optional[str] = None) -> None:
    headers = list(headers)
    frameworks = list(frameworks)
    with NamedTemporaryFile('wt', suffix=SUFFIX) as tmp:
        tmp = Path(tmp.name)
        code = ''
        code += get_frameworks_if_needed(frameworks)
        code += get_headers(headers)
        if member is None:
            code += C_STRUCT_FORMAT.format(highlight=r'\033[1;36m', default=r'\033[0;37m', name=name, member=member)
        else:
            code += C_STRUCT_MEMBER_FORMAT.format(highlight=r'\033[1;36m', default=r'\033[0;37m', name=name,
                                                  member=member)
        tmp.write_text(code)
        build_and_execute(tmp)


@click.command(cls=BaseCommand)
@click.argument('name')
def c_const(headers: List[str], frameworks: List[str], name: str) -> None:
    headers = list(headers)
    frameworks = list(frameworks)
    with NamedTemporaryFile('wt', suffix=SUFFIX) as tmp:
        tmp = Path(tmp.name)
        code = ''
        code += get_frameworks_if_needed(frameworks)
        code += get_headers(headers)
        code += C_CONST_FORMAT.format(name=name)
        tmp.write_text(code)
        build_and_execute(tmp)
