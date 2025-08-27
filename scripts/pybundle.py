#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2016 Stefan Lengfeld

import re
import sys

p = re.compile(b"#\\s*-+8<-+")

# TODO replace with regex or shell glob
strip_lines = set([b"#!/usr/bin/env python3\n",
                   b"# SPDX-License-Identifier: GPL-2.0-only\n",
                   b"# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld\n"])


def do_file(filename):
    with open(filename, "br") as f:
        # Cannot use sys.stdout.write because that's a different internal
        # buffer than sys.stdout.buffer.write.
        sys.stdout.buffer.write(b"\n")
        sys.stdout.buffer.write(b"# bundler: file " + filename.encode("ascii") + b'\n')
        sys.stdout.buffer.write(b"\n")

        cut_on = False
        for line in f:
            if line in strip_lines:
                continue

            if p.match(line):
                if not cut_on:
                    # cut was off, insert note about cut
                    sys.stdout.buffer.write(b"# bundler: --8<-- was here\n")
                cut_on = not cut_on
            else:
                if not cut_on:
                    # cannot use print, beacuse print accepts only a string. A
                    # byte object converted with repr before.
                    sys.stdout.buffer.write(line)


def main():
    sys.stdout.buffer.write(b"""\
#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld
""")
    for filename in sys.argv[1:]:
        do_file(filename)
    return 0


if __name__ == '__main__':
    sys.exit(main())
