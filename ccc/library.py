#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""library.py

macros, wordlists, and queries, read from a library directory and / or
defined in memory

"""
import copy
import logging
import os
import re
from glob import glob
from tempfile import gettempdir

from .cache import generate_idx
from .cqpy import cqpy_dumps, cqpy_load

logger = logging.getLogger(__name__)

NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SIGNATURE_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\(([^()]*)\)$")
QUERY_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")


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
    """Macros, wordlists, and queries for CQP.

    Definitions are taken from
    - a library directory (lib_dir/wordlists/*.txt, lib_dir/macros/*.txt,
      lib_dir/queries/*.cqpy)
    - in-memory definitions (which take precedence)

    In-memory wordlists and macros are written to content-addressed
    files and loaded via CQP's `define … < "file"`, which avoids
    escaping issues and limits on command length.

    Queries are not loaded into CQP; they are stored in CQPY format
    (see ccc.cqpy) and can be run via Corpus.run_query().

    """

    def __init__(self, lib_dir=None, wordlists=None, macros=None, queries=None):
        """
        :param str lib_dir: /path/to/macros/and/wordlists/
        :param dict wordlists: {name: [item, ...]}
        :param dict macros: {name or signature: body}
        :param dict queries: {name: CQP query (str) or CQPY query (dict)}

        """

        self.lib_dir = lib_dir
        self.wordlists = dict()
        self.macros = dict()
        self.queries = dict()

        for name, items in (wordlists or dict()).items():
            self.add_wordlist(name, items)
        for name, body in (macros or dict()).items():
            self.add_macro(name, body)
        for name, query in (queries or dict()).items():
            self.add_query(name, query)

    def __str__(self):

        return '\n'.join([
            f'lib_dir:   {self.lib_dir}',
            f'wordlists: {", ".join("$" + n for n in self.wordlists)}',
            f'macros:    {", ".join("/" + n for n in self.macros)}',
            f'queries:   {", ".join(self.queries)}'
        ])

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        """Number of in-memory definitions that are loaded into CQP
        (i.e. wordlists and macros, but not queries)."""
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

    def add_query(self, name, query):
        """Store a query in memory.

        :param str name: name of query
        :param query: CQP query (str) or CQPY query (dict with key 'cqp' and
                      optional keys 'meta', 'query', 'anchors', 'display')

        """

        if not QUERY_NAME_PATTERN.match(name):
            raise ValueError(f'invalid query name "{name}"')
        if isinstance(query, str):
            query = {'cqp': query}
        elif not isinstance(query, dict) or 'cqp' not in query:
            raise ValueError("query must be str or dict with key 'cqp'")

        self.queries[name] = copy.deepcopy(query)

    def get_query(self, name):
        """Get a query (in-memory definitions take precedence over lib_dir).

        :param str name: name of query

        :return: CQPY query (a copy, so that modifications don't propagate)
        :rtype: dict

        """

        if name in self.queries:
            return copy.deepcopy(self.queries[name])

        paths = self.query_paths()
        if name in paths:
            return cqpy_load(paths[name])

        raise KeyError(f'query "{name}" not defined')

    def available_queries(self):
        """Names of all queries (in lib_dir and in memory).

        :rtype: list

        """

        return sorted(set(self.query_paths()) | set(self.queries))

    def remove_wordlist(self, name):
        self.wordlists.pop(name.lstrip("$"), None)

    def remove_macro(self, name, n_args=None):
        name, n_args, _ = parse_macro_signature(name, n_args)
        self.macros.pop(f"{name}({n_args})", None)

    def remove_query(self, name):
        self.queries.pop(name, None)

    def copy(self):
        """Get a copy (so that modifications don't propagate)."""

        library = Library(self.lib_dir)
        library.wordlists = {name: list(items) for name, items in self.wordlists.items()}
        library.macros = dict(self.macros)
        library.queries = copy.deepcopy(self.queries)
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

    def query_paths(self):
        """Paths of queries in lib_dir.

        :return: {name: path}
        :rtype: dict

        """

        if self.lib_dir is None:
            return dict()

        return {
            os.path.splitext(os.path.basename(path))[0]: os.path.abspath(path)
            for path in sorted(glob(os.path.join(self.lib_dir, 'queries', '*.cqpy')))
        }

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
        wordlist, one file per macro name, and one CQPY file per query),
        so that they can be used via lib_dir later on.

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

        for name, query in self.queries.items():
            path = os.path.join(lib_dir, 'queries', f'{name}.cqpy')
            files[path] = cqpy_dumps(query)

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
