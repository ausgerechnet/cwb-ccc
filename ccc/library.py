#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""library.py

macros and wordlists, read from a library directory and / or defined
in memory

"""
import logging
import os
import re
from glob import glob
from tempfile import gettempdir

from .cache import generate_idx

logger = logging.getLogger(__name__)

NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SIGNATURE_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\(([^()]*)\)$")


def parse_show_macro(cqp_output):
    """Get macro signatures from output of CQP's `show macro`.

    :param str cqp_output: output of `show macro`

    :return: signatures such as '/np(0)'
    :rtype: list

    """

    return [line.strip() for line in cqp_output.split("\n") if line.strip().startswith("/")]


def parse_show_var(cqp_output):
    """Get names of wordlists from output of CQP's `show var`.

    :param str cqp_output: output of `show var`

    :return: names such as '$parties'
    :rtype: list

    """

    lines = [line.strip() for line in cqp_output.split("\n")]
    return sorted(line.rstrip(" =") for line in lines if line.startswith("$") and line.endswith(" ="))


def generate_library_idx(lib_dir, prefix='', length=10):
    """Generate an ID for the wordlists and macros in lib_dir.

    :param str lib_dir: /path/to/macros/and/wordlists/

    :return: identifier
    :rtype: str

    """

    return Library(lib_dir).lib_idx(prefix, length)


def parse_macro_signature(name, n_args=None):
    """Get name, number of arguments, and CQP signature of a macro.

    Accepts either a plain name (+ n_args) or a full signature such
    as 'np(0)' or 'ap($0=Adj)'.

    :param str name: name or signature of macro
    :param int n_args: number of arguments (only for plain names)

    :return: name, n_args, signature
    :rtype: tuple

    """

    name = name.lstrip("/")

    if NAME_PATTERN.match(name):
        n_args = 0 if n_args is None else int(n_args)
        return name, n_args, f"{name}({n_args})"

    match = SIGNATURE_PATTERN.match(name)
    if match is None:
        raise ValueError(f'invalid macro name "{name}"')
    if n_args is not None:
        raise ValueError("n_args cannot be given together with a full signature")

    name, args = match.group(1), match.group(2).strip()
    if args == "" or args.isdigit():
        n_args = int(args) if args else 0
        return name, n_args, f"{name}({n_args})"

    n_args = len(re.findall(r"\$\d+", args))
    return name, n_args, f"{name}({args})"


class Library:
    """Macros and wordlists for CQP.

    Definitions are taken from
    - a library directory (lib_dir/wordlists/*.txt, lib_dir/macros/*.txt)
    - in-memory definitions (which take precedence)

    In-memory definitions are written to content-addressed files and
    loaded via CQP's `define … < "file"`, which avoids escaping issues
    and limits on command length.

    """

    def __init__(self, lib_dir=None, wordlists=None, macros=None):
        """
        :param str lib_dir: /path/to/macros/and/wordlists/
        :param dict wordlists: {name: [item, ...]}
        :param dict macros: {name or signature: body}

        """

        self.lib_dir = lib_dir
        self.wordlists = dict()
        self.macros = dict()

        for name, items in (wordlists or dict()).items():
            self.add_wordlist(name, items)
        for name, body in (macros or dict()).items():
            self.add_macro(name, body)

    def __str__(self):

        return '\n'.join([
            f'lib_dir:   {self.lib_dir}',
            f'wordlists: {", ".join("$" + n for n in self.wordlists)}',
            f'macros:    {", ".join("/" + n for n in self.macros)}'
        ])

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        """Number of in-memory definitions."""
        return len(self.wordlists) + len(self.macros)

    def add_wordlist(self, name, items):
        """Define a wordlist in memory.

        :param str name: name of wordlist (with or without leading '$')
        :param list items: items of the wordlist

        """

        name = name.lstrip("$")
        if not NAME_PATTERN.match(name):
            raise ValueError(f'invalid wordlist name "{name}"')
        if isinstance(items, str):
            raise TypeError("items must be an iterable of str, not str")

        items = [str(item) for item in items]
        for item in items:
            if "\n" in item or "\r" in item:
                raise ValueError(f'wordlist item contains line break: "{item}"')

        self.wordlists[name] = items

    def add_macro(self, name, body, n_args=None):
        """Define a macro in memory.

        :param str name: name of macro, or full signature such as 'np(0)'
        :param str body: CQP query; arguments are referred to as $0, $1, …
        :param int n_args: number of arguments (only for plain names)

        """

        name, n_args, signature = parse_macro_signature(name, n_args)
        key = f"{name}({n_args})"
        self.macros[key] = (signature, body.strip())

    def remove_wordlist(self, name):
        self.wordlists.pop(name.lstrip("$"), None)

    def remove_macro(self, name, n_args=None):
        name, n_args, _ = parse_macro_signature(name, n_args)
        self.macros.pop(f"{name}({n_args})", None)

    def copy(self):
        """Get a copy (so that modifications don't propagate)."""

        library = Library(self.lib_dir)
        library.wordlists = {name: list(items) for name, items in self.wordlists.items()}
        library.macros = dict(self.macros)
        return library

    def lib_idx(self, prefix='', length=10):
        """Identifier of definitions in lib_dir (file names and contents).

        """

        wordlists, macros = self.paths()
        paths = sorted(list(wordlists.values()) + macros)
        identifiers = list()
        for path in paths:
            with open(path, 'rt', encoding='utf-8') as f:
                identifiers.append((os.path.relpath(path, self.lib_dir), f.read()))

        return generate_idx(identifiers, prefix, length)

    def idx(self, prefix='', length=10):
        """Identifier of in-memory definitions; None if there are none.

        Definitions in lib_dir are identified via the data directory
        (see cwb.init_data_dir).

        """

        if len(self) == 0:
            return None

        identifiers = (
            [("$" + name, items) for name, items in sorted(self.wordlists.items())] +
            [("/" + key, macro) for key, macro in sorted(self.macros.items())]
        )
        return generate_idx(identifiers, prefix, length)

    def paths(self):
        """Paths of wordlists and macros in lib_dir.

        :return: wordlists (as {name: path}), macros (list of paths)
        :rtype: tuple

        """

        if self.lib_dir is None:
            return dict(), list()

        wordlists = dict()
        for path in sorted(glob(os.path.join(self.lib_dir, 'wordlists', '*.txt'))):
            name = os.path.splitext(os.path.basename(path))[0]
            wordlists[name] = os.path.abspath(path)
        macros = [
            os.path.abspath(path) for path in sorted(glob(os.path.join(self.lib_dir, 'macros', '*.txt')))
        ]

        return wordlists, macros

    def cqp_commands(self, directory=None):
        """Get CQP commands that define all wordlists and macros. In-memory
        definitions are written to files in directory first.

        :param str directory: where to write in-memory definitions

        :return: CQP commands
        :rtype: list

        """

        # directory for in-memory definitions
        if directory is None:
            directory = os.path.join(gettempdir(), "ccc-library")
        if len(self) > 0:
            os.makedirs(directory, exist_ok=True)

        wordlists, macros = self.paths()

        # in-memory definitions take precedence
        for name, items in self.wordlists.items():
            wordlists[name] = _write(
                directory, f"wordlist-{name}", "".join(item + "\n" for item in items)
            )
        for key, (signature, body) in self.macros.items():
            macros.append(_write(
                directory, f"macro-{key.replace('(', '-').rstrip(')')}",
                f"MACRO {signature}\n{body}\n;\n"
            ))

        commands = [f'define ${name} < "{path}";' for name, path in wordlists.items()]
        commands += [f'define macro < "{path}";' for path in macros]

        return commands

    def load(self, cqp, directory=None):
        """Define all wordlists and macros in a running CQP process.

        :param CQP cqp: CQP process
        :param str directory: where to write in-memory definitions

        """

        for command in self.cqp_commands(directory):
            cqp.Exec(command)

        # for wordlists defined in macros, it is necessary to execute the macro once
        for signature in parse_show_macro(cqp.Exec("show macro;")):
            if signature.endswith("(0)"):
                cqp.Exec(signature.split("(")[0] + "();")

    def save(self, lib_dir, overwrite=False):
        """Save in-memory definitions to a library directory (one file per
        wordlist and one file per macro name), so that they can be
        used via lib_dir later on.

        :param str lib_dir: /path/to/macros/and/wordlists/
        :param bool overwrite: overwrite existing files?

        :return: paths of written files
        :rtype: list

        """

        files = dict()
        for name, items in self.wordlists.items():
            path = os.path.join(lib_dir, 'wordlists', f'{name}.txt')
            files[path] = "".join(item + "\n" for item in items)

        # macros with the same name (but different number of arguments) share one file
        for key, (signature, body) in sorted(self.macros.items()):
            path = os.path.join(lib_dir, 'macros', f'{key.split("(")[0]}.txt')
            files[path] = files.get(path, "") + f"MACRO {signature}\n{body}\n;\n\n"

        if not overwrite:
            existing = [path for path in files if os.path.exists(path)]
            if len(existing) > 0:
                raise FileExistsError(f'files already exist: {", ".join(existing)}')

        for path, content in files.items():
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wt', encoding='utf-8') as f:
                f.write(content)

        return list(files.keys())


def _write(directory, stem, content):
    """Write content to a content-addressed file (if it does not exist yet).

    :return: absolute path
    :rtype: str

    """

    path = os.path.abspath(
        os.path.join(directory, f"{stem}-{generate_idx([content], length=10)}.txt")
    )
    if not os.path.isfile(path):
        tmp_path = f"{path}.{os.getpid()}.tmp"
        with open(tmp_path, "wt", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)

    return path
