#! /usr/bin/env python
# -*- coding: utf-8 -*-


# Version 2.0 of "PyCQP" by Joerg Asmussen, DSL (Febr. 2008)
# Some changes by Philipp Heinrich (2020)


import sys
import os
import re
import random
import time
import subprocess
import select
import signal
from io import StringIO
from pandas import read_csv, DataFrame
from tempfile import NamedTemporaryFile
import threading
import logging
logger = logging.getLogger(__name__)


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


# GLOBAL CONSTANTS OF MODULE:
cProgressControlCycle = 5   # secs between each progress control cycle
cMaxRequestProcTime = 500   # max secs for processing a user request


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
        """Control the progess.

        CREATED: 2008-02

        This method is run as a thread.
        At certain intervals (cProgressControlCycle), it controls how long the
        CQP process of the current user has spent on processing this user's
        latest CQP command. If this time exceeds a certain maximun
        (cMaxRequestProcTime), this method kills the CQP process.
        """
        self.runController = True
        while self.runController:
            time.sleep(cProgressControlCycle)
            if self.execStart is not None:
                if time.time() - self.execStart > cMaxRequestProcTime *\
                 self.maxProcCycles:
                    print(
                        '''WARNING!: PROGRESS CONTROLLER IDENTIFIED BLOCKING CQP
                        PROCESS ID {}'''.format(self.CQP_process.pid), end='')
                    # os.kill(self.CQP_process.pid, SIGKILL) - doesn't work!
                    os.popen("kill -9 " + str(self.CQP_process.pid))  # works!
                    print("=> KILLED!")
                    self.CQPrunning = False
                    break

    def __kill__(self):
        self.Terminate()
        os.killpg(os.getpgid(self.CQP_process.pid), signal.SIGTERM)
        self.__del__()

    def __init__(self, bin="/usr/local/bin/cqp", options='-c'):
        """Class constructor."""
        self.execStart = time.time()
        self.maxProcCycles = 1.0

        # start CQP as a child process of this wrapper
        if bin is None:
            print("ERROR: Path to CQP binaries undefined", file=sys.stderr)
            sys.exit(1)
        self.CQP_process = subprocess.Popen(bin + ' ' + options,
                                            shell=True,
                                            stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            universal_newlines=True,
                                            close_fds=True,
                                            preexec_fn=os.setsid)
        self.CQPrunning = True

        # init progress controller
        progressthread = threading.Thread(
            target=self._progressController, args=()
        )
        progressthread.setDaemon(True)
        progressthread.start()

        # "cqp -c" should print version on startup:
        version_string = self.CQP_process.stdout.readline()
        version_string = version_string.rstrip()  # Equivalent to Perl's chomp
        self.CQP_process.stdout.flush()
        print(version_string, file=sys.stderr)
        version_regexp = re.compile(
            r'^CQP\s+(?:\w+\s+)*([0-9]+)\.([0-9]+)(?:\.b?([0-9]+))?(?:\s+(.*))?$'
        )
        match = version_regexp.match(version_string)
        if not match:
            print("ERROR: CQP backend startup failed", file=sys.stderr)
            sys.exit(1)
        self.major_version = int(match.group(1))
        self.minor_version = int(match.group(2))
        self.beta_version = int(match.group(3))
        self.compile_date = match.group(4)

        # We need cqp-2.2.b41 or newer (for query lock):
        if not (
                self.major_version >= 3 or
                (self.major_version == 2 and
                    self.minor_version == 2 and
                    self.beta_version >= 41)
                ):
            print(
                "ERROR: CQP version too old: " + version_string,
                file=sys.stderr)
            sys.exit(1)

        # Error handling:
        self.error_handler = None
        self.status = 'ok'
        self.error_message = ''  # we store compound error messages as a STRING
        self.errpipe = self.CQP_process.stderr.fileno()

        # Debugging (prints more or less everything on stdout)
        self.debug = False

        # CQP defaults:
        self.Exec('set PrettyPrint off')
        self.execStart = None

    def Terminate(self):
        """Terminate controller thread, must be called before deleting CQP."""
        self.execStart = None
        self.runController = False

    def SetProcCycles(self, procCycles):
        """Set procCycles."""
        print("    Setting procCycles to {}".format(procCycles))
        self.maxProcCycles = procCycles
        return int(self.maxProcCycles * cMaxRequestProcTime)

    def __del__(self):
        """Stop running CQP instance."""
        if self.CQPrunning:
            # print "Deleting CQP with pid", self.CQP_process.pid, "...",
            self.CQPrunning = False
            self.execStart = time.time()
            if self.debug:
                print("Shutting down CQP backend ...", end='')
            self.CQP_process.stdin.write('exit;')  # exits CQP backend
            if self.debug:
                print("Done\nCQP object deleted.")
            self.execStart = None
            # print "Finished"

    def Exec(self, cmd):
        """Execute CQP command.

        The method takes as input a command string and sends it
        to the CQP child process
        """
        self.execStart = time.time()
        self.status = 'ok'
        cmd = cmd.rstrip()  # Equivalent to Perl's 'chomp'
        cmd = re.sub(r';\s*$', r'', cmd)
        if self.debug:
            print("CQP <<", cmd + ";")
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
                if self.debug:
                    print("CQP " + "-" * 60)
                break
            if self.debug:
                print("CQP >> " + ln)
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
            sys.stderr.write(
                            "ERROR: Invalid value for first (" +
                            str(first) + ") or last (" + str(last) +
                            ") line in Dump() method\n")
            sys.exit(1)
        elif isinstance(first, int) and isinstance(last, int):
            if first > last:
                sys.stderr.write(
                    "ERROR: Invalid value for first line (first = " +
                    str(first) + " > last = " + str(last) +
                    ") in Dump() method\n")
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

        # convert to dataframe
        df = read_csv(StringIO(result),
                      sep="\t", header=None, index_col=[0, 1],
                      names=["match", "matchend", "target", "keyword"])
        df = df.astype(int)
        return df

    def Undump(self, subcorpus="tmp", df=DataFrame()):
        """Undump named query result from table of corpus positions."""
        columns = []
        wth = ''
        if 'target' in df.columns:
            wth = 'with target '
            columns = ['target']
            if 'keyword' in df.columns:
                wth = 'with target keyword '
                columns = ['target', 'keyword']
        with NamedTemporaryFile(mode='wt') as f:
            f.write(str(len(df)) + "\n")
            df.to_csv(f, mode="a", sep="\t", columns=columns, header=None)
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
            print(
                "ERROR: Invalid key '" + spec1 + "' in Group() method",
                file=sys.stderr)
            sys.exit(1)
        spec1 = match.group(1) + ' ' + match.group(2)
        if spec2 != '':
            match = re.match(spec_regexp, spec2)
            if not match:
                print(
                    "ERROR: Invalid key '" + spec2 + "' in Group() method",
                    file=sys.stderr)
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
            print(
                "ERROR: Parameter 'sort_clause' undefined in Count() method",
                file=sys.stderr)
            sys.exit(1)
        return self.Exec(
            'count ' +
            subcorpus +
            ' by ' +
            sort_clause +
            ' cut ' +
            str(cutoff))

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
            print(msg, file=sys.stderr)

    def Set_error_handler(self, handler=None):
        """Set user-defined error handler."""
        self.error_handler = handler

    def Debug(self, on=False):
        """Switch debugging output on/off."""
        prev = self.debug
        self.debug = on
        return prev

    def nqr_activate(self, corpus_name, name=None):

        if name is not None:
            logger.info('activating NQR "%s:%s"' % (corpus_name, name))
            self.Exec(name)
        else:
            logger.info('activating corpus "%s"' % corpus_name)
            self.Exec(corpus_name)

    def nqr_save(self, corpus_name, name='Last'):
        """Saves subcorpus to disk.

        :param str name: named subcorpus to save

        """
        logger.info(
            'saving NQR "%s:%s" to disk' % (corpus_name, name)
        )
        self.Exec("save %s;" % name)

    def nqr_from_query(self, query, name='Last',
                       match_strategy='longest',
                       return_dump=True):
        """Defines subcorpus from query, returns dump.

        :param str query: valid CQP query
        :param str name: subcorpus name
        :param str match_strategy: CQP matching strategy

        :return: df_dump
        :rtype: DataFrame

        """
        logger.info(
            'defining NQR "%s" from query' % name
        )
        self.Query('%s=%s;' % (name, query))

        if return_dump:
            logger.info('dumping result')
            df_dump = self.Dump(name)
            return df_dump

    def nqr_from_dump(self, df_dump, name='Last'):
        """Defines subcorpus from dump.

        :param DataFrame df_dump: DataFrame indexed by (match, matchend)
                                  with optional columns 'target' and 'keyword'
        :param str name: subcorpus name

        """
        logger.info(
            'defining NQR "%s" from dump ' % name
        )
        self.Undump(name, df_dump)
