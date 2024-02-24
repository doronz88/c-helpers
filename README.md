# C-Helpers

## Overview

Just like the old saying ["girls just wanna have fun"](https://www.youtube.com/watch?v=PIb6AZdTr-A), so do software
researchers.

Many of us sometimes need to just get the values of some basic C native types. We can look for them in the headers or
just compile a simple C program to print them - which can be quite exhausting each time.

That's where `c-helpers` comes into place - Simply use the `c-const` and `c-struct` directly from your terminal!

For example:

```shell
$ c-struct 'struct dirent'
sizeof(struct dirent): 1048 (0x418)

$ c-struct 'struct dirent' d_ino
sizeof(struct dirent): 1048 (0x418)
offsetof(struct dirent, d_ino): 0 (0x00)
sizeof(struct dirent::d_ino): 8 (0x08)

$ c-const EAGAIN
35 (0x23)
```

## Installation

```shell
python3 -m pip install c-helpers
```
