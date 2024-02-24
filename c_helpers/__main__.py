import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

import click
from plumbum import local

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


def get_libraries_if_needed() -> str:
    result = ''
    if os.uname().sysname == 'Darwin':
        for framework in FRAMEWORKS:
            result += f'@import {framework};\n'
    return result


def get_headers() -> str:
    result = ''
    for header in HEADERS:
        result += f'#include <{header}>\n'
    return result


@click.command()
@click.argument('name')
@click.argument('member', required=False)
def c_struct(name: str, member: Optional[str] = None) -> None:
    with NamedTemporaryFile('wt', suffix=SUFFIX) as tmp:
        tmp = Path(tmp.name)
        code = ''
        code += get_libraries_if_needed()
        code += get_headers()
        if member is None:
            code += C_STRUCT_FORMAT.format(highlight=r'\033[1;36m', default=r'\033[0;37m', name=name, member=member)
        else:
            code += C_STRUCT_MEMBER_FORMAT.format(highlight=r'\033[1;36m', default=r'\033[0;37m', name=name,
                                                  member=member)
        tmp.write_text(code)
        out_file = f'{tmp.absolute()}.out'
        clang(tmp.absolute(), '-o', out_file, '-fmodules', '-fcxx-modules')
        print(local[out_file]())


@click.command()
@click.argument('name')
def c_const(name: str) -> None:
    with NamedTemporaryFile('wt', suffix=SUFFIX) as tmp:
        tmp = Path(tmp.name)
        code = ''
        code += get_libraries_if_needed()
        code += get_headers()
        code += C_CONST_FORMAT.format(name=name)
        tmp.write_text(code)
        out_file = f'{tmp.absolute()}.out'
        clang(tmp.absolute(), '-o', out_file, '-fmodules', '-fcxx-modules')
        print(local[out_file]())
