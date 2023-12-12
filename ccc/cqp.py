#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""cqp.py

access to CQP

original version by Joerg Asmussen (2008)
current version by Philipp Heinrich (2023)

"""
import logging
import os
import random
import re
import select
import subprocess
import sys
import threading
import time
from glob import glob
from io import StringIO
from tempfile import NamedTemporaryFile

# requirements
from pandas import DataFrame, read_csv

logger = logging.getLogger(__name__)


# GLOBAL CONSTANTS OF MODULE:
CPROGRESSCONTROLCYCLE = 5   # secs between each progress control cycle
CMAXREQUESTPROCTIME = 900   # max secs for processing a user request


# ERROR MESSAGE TYPES:
class ErrCQP:
    """Handle CQP error message."""
    def __init__(self, msg):
        """Class constructor."""
        self.msg = msg.rstrip()


class ErrKilled:
    """Handle errors when process is killed."""
    def __init__(self, msg):
        """Class constructor."""
        self.msg = msg.rstrip()


# ACTUAL INTERFACE:
class CQP:
    """Wrapper for CQP."""

    def _progressController(self):
        """Control the progress.

        CREATED: 2008-02

        This method is run as a thread.
        At certain intervals (CPROGRESSCONTROLCYCLE), it controls how long the
        CQP process of the current user has spent on processing this user's
        latest CQP command. If this time exceeds a certain maximum
        (CMAXREQUESTPROCTIME), this method kills the CQP process.
        """
        self.runController = True
        while self.runController:
            time.sleep(CPROGRESSCONTROLCYCLE)
            if self.execStart is not None:
                if time.time() - self.execStart > CMAXREQUESTPROCTIME * self.maxProcCycles:
                    logger.error(f"progress controller identified blocking cqp process id {self.CQP_process.pid}")
                    os.popen("kill -9 " + str(self.CQP_process.pid))
                    self.CQPrunning = False
                    self.execStart = None
                    logger.error("-- CQP process killed!")
                    break

    def __init__(self, binary="cqp", options='-c', print_version=False):
        """Class constructor."""
        self.execStart = time.time()
        self.maxProcCycles = 1.0

        # start CQP as a child process of this wrapper
        if binary is None:
            logger.error("path to CQP binaries undefined")
            sys.exit(1)
        self.CQP_process = subprocess.Popen(binary + ' ' + options,
                                            shell=True,
                                            stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            universal_newlines=True,
                                            close_fds=True,
                                            preexec_fn=os.setsid)
        self.CQPrunning = True

        # init progress controller
        progressthread = threading.Thread(target=self._progressController, args=())
        progressthread.daemon = True
        progressthread.start()

        # "cqp -c" should print version on startup:
        version_string = self.CQP_process.stdout.readline()
        version_string = version_string.rstrip()  # Equivalent to Perl's chomp
        self.CQP_process.stdout.flush()
        if print_version:
            print(version_string)
        logger.debug("CQP " + "-" * 43 + " started")
        version_regexp = re.compile(
            r'^CQP\s+(?:\w+\s+)*([0-9]+)\.([0-9]+)(?:\.b?([0-9]+))?(?:\s+(.*))?$'
        )
        match = version_regexp.match(version_string)
        if not match:
            logger.error("CQP backend startup failed")
            sys.exit(1)
        self.major_version = int(match.group(1))
        self.minor_version = int(match.group(2))
        self.beta_version = int(match.group(3))
        self.compile_date = match.group(4)

        # We need cqp-2.2.b41 or newer (for query lock):
        if not (self.major_version >= 3 or (self.major_version == 2 and
                                            self.minor_version == 2 and
                                            self.beta_version >= 41)):
            logger.error("CQP version too old: " + version_string)
            sys.exit(1)

        # Error handling:
        self.error_handler = None
        self.status = 'ok'
        self.error_message = ''  # we store compound error messages as a STRING
        self.errpipe = self.CQP_process.stderr.fileno()

        # CQP defaults:
        self.Exec('set PrettyPrint off')
        self.execStart = None

    def SetProcCycles(self, procCycles):
        """Set procCycles."""
        print(f"    Setting procCycles to {procCycles}")
        self.maxProcCycles = procCycles
        return int(self.maxProcCycles * CMAXREQUESTPROCTIME)

    def __del__(self):
        """Stop running CQP instance."""
        if self.CQPrunning:
            logger.debug("Shutting down CQP backend ...")
            self.runController = False
            self.execStart = time.time()
            self.CQP_process.stdin.write('exit;')
            self.CQP_process.stdin.flush()
            del self.CQP_process
            self.CQPrunning = False
            self.execStart = None
            logger.debug("... -- CQP object deleted.")

    def Exec(self, cmd):
        """Execute CQP command.

        The method takes as input a command string and sends it
        to the CQP child process
        """
        self.execStart = time.time()
        self.status = 'ok'
        cmd = cmd.rstrip()  # Equivalent to Perl's 'chomp'
        cmd = re.sub(r';\s*$', r'', cmd)
        logger.debug("CQP << " + cmd + ";")
        try:
            self.CQP_process.stdin.write(cmd + '; .EOL.;\n')
        except IOError:
            return None
        # In CQP.pm lines are appended to a list @result.
        # This implementation prefers a string structure instead
        # because output from this module is meant to be transferred
        # accross a server connection. To enable the development of
        # client modules written in any language, the server only emits
        # strings which then are to be structured by the client module.
        # The server does not emit pickled data according to some
        # language dependent protocol.
        self.CQP_process.stdin.flush()
        result = []
        while self.CQPrunning:
            ln = self.CQP_process.stdout.readline()
            ln = ln.strip()  # strip off whitespace from start and end of line
            if re.match(r'-::-EOL-::-', ln):
                logger.debug("CQP " + "-" * 40 + " terminated")
                break
            logger.debug("CQP >> " + ln)
            if ln != '':
                result.append(ln)
            self.CQP_process.stdout.flush()
        self.Checkerr()
        self.execStart = None
        result = '\n'.join(result)
        result = result.rstrip()  # strip off whitespace from EOL (\n)
        return result

    def Query(self, query):
        """Execute query in safe mode (query lock)."""
        result = []
        key = str(random.randint(1, 1000000))
        errormsg = ''  # collect CQP error messages AS STRING
        ok = True      # check if any error occurs
        self.Exec('set QueryLock ' + key)  # enter query lock mode
        if self.status != 'ok':
            errormsg = errormsg + self.error_message
            ok = False
        result = self.Exec(query)
        if self.status != 'ok':
            errormsg = errormsg + self.error_message.decode('utf-8')
            ok = ok and False
        self.Exec('unlock ' + key)  # unlock with random key
        if self.status != 'ok':
            errormsg = errormsg + self.error_message
            ok = ok and False
        # Set error status & error message:
        if ok:
            self.status = 'ok'
        else:
            self.status = 'error'
            self.error_message = errormsg
        return result

    def Dump(self, subcorpus='Last', first=None, last=None):
        """Dump named query result into table of corpus positions."""

        # check first and last
        if first is None and last is None:
            # actual dump
            result = self.Exec('dump ' + subcorpus + ";")

        elif ((not isinstance(first, int) and first is not None) or
              (not isinstance(last, int) and last is not None)):
            logger.error("Invalid value for first (" + str(first) +
                         ") or last (" + str(last) + ") line in Dump() method")
            sys.exit(1)
        elif isinstance(first, int) and isinstance(last, int):
            if first > last:
                logger.error("Invalid value for first line (first = " +
                             str(first) + " > last = " + str(last) +
                             ") in Dump() method")
                sys.exit(1)
        else:
            if first is not None and last is None:
                last = first
            elif last is not None and first is None:
                first = last
            # actual dump
            result = self.Exec(
                'dump ' + subcorpus + " " + str(first) + " " + str(last) + ";"
            )

        # convert to pandas dataframe
        df = read_csv(StringIO(result),
                      sep="\t", header=None, index_col=[0, 1],
                      names=["match", "matchend", "target", "keyword"])
        df = df.astype(int)

        return df

    def Undump(self, subcorpus="Last", df=DataFrame()):
        """Undump named query result from table of corpus positions."""

        columns = ['match', 'matchend']
        wth = ''
        if 'target' in df.columns:
            wth = 'with target '
            columns = columns + ['target']
            if 'keyword' in df.columns:
                wth = 'with target keyword '
                columns = columns + ['target', 'keyword']

        with NamedTemporaryFile(mode='wt') as f:
            f.write(str(len(df)) + "\n")
            df.reset_index().to_csv(f, mode="a", sep="\t", columns=columns, header=None, index=False)
            f.seek(0)
            f.flush()
            self.Exec("undump " + subcorpus + " " + wth + '< "' + f.name + '";')

    def Group(self, subcorpus='Last',
              spec1='match.word', spec2='', cutoff='1'):
        """Compute frequency distribution over attribute values.

        (single values or pairs) using group command.

        Note that the arguments are specified in the logical order,
        in contrast to "group"
        """
        spec2_regexp = re.compile(r'^[0-9]+$')
        if spec2_regexp.match(spec2):
            cutoff = spec2
            spec2 = ''
        spec_regexp = re.compile(
          r'^(match|matchend|target[0-9]?|keyword)\.([A-Za-z0-9_-]+)$'
        )
        match = re.match(spec_regexp, spec1)
        if not match:
            logger.error("Invalid key '" + spec1 + "' in Group() method")
            sys.exit(1)
        spec1 = match.group(1) + ' ' + match.group(2)
        if spec2 != '':
            match = re.match(spec_regexp, spec2)
            if not match:
                logger.error("Invalid key '" + spec2 + "' in Group() method")
                sys.exit(1)
            spec2 = match.group(1) + ' ' + match.group(2)
            cmd = 'group ' + subcorpus + ' ' + spec2 + ' by ' + spec1 + \
                  ' cut ' + cutoff
        else:
            cmd = 'group ' + subcorpus + ' ' + spec1 + ' cut ' + cutoff
        result = self.Exec(cmd)
        return result

    def Count(self, subcorpus='Last', sort_clause=None, cutoff=1):
        """Compute frequency distribution for match strings.

        Based on sort clause.
        """
        if sort_clause is None:
            logger.error("Parameter 'sort_clause' undefined in Count() method")
            sys.exit(1)
        return self.Exec('count ' + subcorpus +
                         ' by ' + sort_clause +
                         ' cut ' + str(cutoff))

    def Checkerr(self):
        """Check CQP's stderr stream for error messages.

        (returns true if there was an error).
        OBS! In CQP.pm the error_message is stored in a list,
        In PyCQP_interface.pm we use a string (which better can be sent
        accross the server line).
        """
        ready = select.select([self.errpipe], [], [], 0)
        if self.errpipe in ready[0]:
            # We've got something on stderr -> an error must have occurred:
            self.status = 'error'
            self.error_message = self.Readerr()
        return not self.Ok()

    def Readerr(self):
        """Read all available lines from CQP's stderr stream."""
        return os.read(self.errpipe, 16384)

    def Status(self):
        """Read the CQP object's (error) status."""
        return self.status

    def Ok(self):
        """Simplified interface for checking for CQP errors."""
        if self.CQPrunning:
            return (self.Status() == 'ok')
        else:
            return False

    def Error_message(self):
        """Return the CQP error message."""
        if self.CQPrunning:
            return ErrCQP(self.error_message)
        else:
            msgKilled = '**** CQP KILLED ***\n\
            CQP COULD NOT PROCESS YOUR REQUEST\n'
            return ErrKilled(msgKilled + self.error_message)

    def Error(self, msg):
        """Processe/output error messages.

        (optionally run through user-defined error handler)
        """
        if self.error_handler is not None:
            self.error_handler(msg)
        else:
            logger.error(msg)

    def Set_error_handler(self, handler=None):
        """Set user-defined error handler."""
        self.error_handler = handler

    #########################
    # SOME ALIASES FOR NQRs #
    #########################
    def nqr_from_query(self, query, name='Last',
                       match_strategy='longest', return_dump=True,
                       propagate_error=False):
        """Defines NQR from query, optionally returns dump.

        :param str query: valid CQP query
        :param str name: name for NQR
        :param str match_strategy: CQP matching strategy
        :param bool return_dump: whether to return the dump

        :return: df_dump
        :rtype: DataFrame

        """
        name = 'Last' if name is None else name

        logger.info(f'defining NQR "{name}" from query: {query}')
        self.Query(f'{name}={query};')

        if not self.Ok():
            logger.error(f'{self.error_message}')
            return self.error_message if propagate_error else DataFrame()

        size = int(self.Exec(f"size {name}"))
        if size == 0:
            logger.info(f'no results for query: {query}')
            return DataFrame() if return_dump else None

        if return_dump:
            logger.info('dumping result')
            df_dump = self.Dump(name)
            return df_dump

    def nqr_from_dump(self, df_dump, name='Last'):
        """Alias for Undump. Defines NQR from given dump.

        :param DataFrame df_dump: DataFrame indexed by (match, matchend)
                                  with optional columns 'target' and 'keyword'
        :param str name: name for NQR

        """
        logger.info(f'defining NQR "{name}" from dump with {len(df_dump)} matches')
        self.Undump(name, df_dump)
        if not self.Ok():
            logger.error('invalid dump')

    def nqr_activate(self, corpus_name, name=None):
        """Activate NQR or whole corpus.

        :param str corpus_name: name of the corpus
        :param str name: name of NQR

        """
        if name is not None:
            logger.info(f'activating NQR "{corpus_name}:{name}"')
            self.Exec(name)

        else:
            logger.info(f'activating corpus "{corpus_name}"')
            self.Exec(corpus_name)

        if not self.Ok():
            logger.error('invalid corpus or NQR')

    def nqr_save(self, corpus_name, name='Last'):
        """Save NQR to disk.

        :param str corpus_name: name of the corpus
        :param str name: nqr to save

        """
        logger.info(f'saving NQR "{corpus_name}:{name}" to disk')
        self.Exec(f"save {name};")
        if not self.Ok():
            logger.error('invalid corpus or NQR')


def start_cqp(cqp_bin, registry_dir,
              data_dir=None, corpus_name=None,
              lib_dir=None, subcorpus_name=None):
    """Start CQP process, activate (sub-)corpus, set directory paths, and
    read library (macros and wordlists).

    :param str cqp_bin: /path/to/cqp-binary
    :param str registry_dir: /path/to/cwb/registry/
    :param str data_dir: /path/to/data/and/cache/
    :param str corpus_name: name of corpus in CWB registry
    :param str lib_dir: /path/to/macros/and/wordlists/
    :param str subcorpus_name: name of subcorpus (NQR)

    :return: CQP process
    :rtype: CQP

    """

    cqp = CQP(
        binary=cqp_bin,
        options='-c -r ' + registry_dir
    )

    if data_dir is not None:
        cqp.Exec(f'set DataDirectory "{data_dir}"')

    if lib_dir is not None:

        # wordlists
        wordlists = glob(os.path.join(lib_dir, 'wordlists', '*.txt'))
        for wordlist in wordlists:
            name = wordlist.split('/')[-1].split('.')[0]
            abs_path = os.path.abspath(wordlist)
            cqp_exec = f'define ${name} < "{abs_path}";'
            cqp.Exec(cqp_exec)

        # macros
        macros = glob(os.path.join(lib_dir, 'macros', '*.txt'))
        for macro in macros:
            abs_path = os.path.abspath(macro)
            cqp_exec = f'define macro < "{abs_path}";'
            cqp.Exec(cqp_exec)
        # for wordlists defined in macros, it is necessary to execute the macro once
        macros = cqp.Exec("show macro;").split("\n")
        for macro in macros:
            # NB: this yields !cqp.Ok() if macro is not zero-valent
            cqp.Exec(macro.split("(")[0] + "();")

    # initialize corpus after macro definition, so execution of macro doesn't spend time
    if corpus_name is not None:
        cqp.Exec(corpus_name)
    if subcorpus_name is not None:
        cqp.Exec(subcorpus_name)

    if not cqp.Ok():
        raise NotImplementedError()

    return cqp
