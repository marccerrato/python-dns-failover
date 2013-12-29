#!/usr/bin/env python
# -*- coding: utf-8 -*-

import errno
import httplib
import os
import select
import signal
import time


class HttpCheck(object):
    """
    Check that a given HTTP test request can be done correctly.
    """
    def __init__(self, method='GET', url='/', body=None, headers={},
                 port=None, useHttps=False, validStatusCodes=[200, 302]):
        self.method = method
        self.url = url
        self.body = body
        self.headers = headers
        if not port:
            port = 80 if not useHttps else 443
        self.port = port
        self.useHttps = useHttps
        self.validStatusCodes = validStatusCodes

    def check(self, ipaddr):
        if self.useHttps:
            connection = httplib.HTTPSConnection(ipaddr, self.port)
        else:
            connection = httplib.HTTPConnection(ipaddr, self.port)

        try:
            connection.request(self.method, self.url, self.body, self.headers)
            response = connection.getresponse()
            return response.status in self.validStatusCodes
        except:
            return False


class TickTimer(object):
    """
    Schedule a check to be executed every *interval* seconds.
    If the check has not returned after *timeout* seconds, kill it.
    The *timeout* is fixed.
    """

    def __init__(self, interval, timeout, retry):
        self.interval = interval
        self.timeout = timeout
        self.retry = retry
        self.last = 0

    def getNextCheckTime(self):
        # Initialization case
        if self.last == 0:
            # Add one second to make sure that the first check is not
            # scheduled in the past
            self.last = time.time() + 1
            return self.last
        # Compute the timestamp of the next check
        self.last += self.interval
        # If we're already late, offset our clock
        if self.last < time.time():
            self.last = time.time()
        return self.last

    def getCheckTimeout(self):
        return self.timeout

    def getRetry(self):
        return self.retry


def boundedCheck(target, check, timer, logger):
    """
    Execute the given *check* on the given *target* (*target* should be an
    IP address). The *timer* is used to retrieve the timeout, and useful
    information will be sent using the *logger*.

    This function will fork(), and the check will be executed in the child
    process. The parent process will wait for the child process, and kill
    it if it did not answer within the timeout specified by the *timer*
    implementation.
    """
    timeout = timer.getCheckTimeout()
    deadline = time.time() + timeout
    logger.debug('[DEBUG] Starting check {0} on {1}, timeout={2}'
                 .format(check, target, timeout))
    # Use self-pipe trick: setup a SIGCHLD handler to write 1 byte to a pipe
    # (and select() on that pipe)
    pipe = os.pipe()

    def sigchld(sig, frame):
        try:
            os.write(pipe[1], ' ')
        except:
            pass

    signal.signal(signal.SIGCHLD, sigchld)
    pid = os.fork()
    if pid:
        # parent process: wait for the child
        while time.time() < deadline:
            timeout = max(0, deadline - time.time())
            try:
                rfds, wfds, efds = select.select([pipe[0]], [], [], timeout)
            except select.error as err:
                if err.args[0] == errno.EINTR:
                    continue
            if rfds:
                # something in the pipe = got a SIGCHLD
                logger.debug('[DEBUG] Child exited, retrieving its status')
                childpid, status = os.wait()
                logger.debug('[DEBUG] Child exit status={0}'.format(status))
                retval = (status == 0)
            else:
                # timeout
                logger.info('[INFO] Child timeout, killing it')
                os.kill(pid, signal.SIGKILL)
                logger.debug('[DEBUG] Reaping child process')
                os.wait()
                retval = False
            os.close(pipe[0])
            os.close(pipe[1])
            logger.debug('[DEBUG] Check result is {0}'.format(retval))
            return retval
    else:
        # child process: do the check
        try:
            if check.check(target):
                exit(0)
            else:
                exit(1)
        except Exception:
            exit(2)


def retryBoundedCheck(target, check, timer, logger):
    retry = timer.getRetry()
    failed = 0
    while True:
        if boundedCheck(target, check, timer, logger):
            # Success!
            if failed:
                # If there were previous failures, log them.
                logger.info('[INFO] Check failed {0} time(s) for target {1} '
                            'before passing.'
                            .format(failed, target))
            return True
        failed += 1
        if failed >= retry:
            logger.info('[INFO] Check failed {0} times for target {1}. '
                        'Giving up.'
                        .format(failed, target))
            return False


def run(fqdns, ip_addresses, dns, check, timer, logger):
    """
    This is the "main loop". It will repeatedly check that the machines
    pointed by the DNS records are fine.
    """
    if isinstance(fqdns, basestring):
        fqdns = [fqdns]

    if isinstance(ip_addresses, basestring):
        ip_addresses = [ip_addresses]

    logger.info('[INFO] Python-dns-failover starting')

    while True:
        now = time.time()
        nextCheck = timer.getNextCheckTime()

        # Log if checking is late
        if now > nextCheck:
            logger.warning('[WARNING] We are late by {0} seconds'
                           .format(now-nextCheck))

        # Wait until newt check time
        while time.time() < nextCheck:
            wait = nextCheck - time.time()
            logger.info('[INFO] Waiting {0} seconds before next round of '
                        'checks'
                        .format(wait))
            time.sleep(wait)

        # For each FQDN of the provided list
        for fqdn in fqdns:
            logger.debug('[DEBUG] Getting DNS records for {0}'
                         .format(fqdn))

            # Get current ip adresses records associated with the FQDN
            try:
                records = dns.get_a_records(fqdn)
            except Exception as e:
                logger.error('[ERROR] Error while retrieving DNS records for '
                             '{0}: {1}'
                             .format(fqdn, e))
                continue
            else:
                logger.debug('[DEBUG] DNS current records: {0}'
                             .format(records))

            logger.debug('[DEBUG] Checking servers')

            # For each ip address of the provided list
            for ip_addr in ip_addresses:

                # Server seems dead
                if not retryBoundedCheck(ip_addr, check, timer, logger):

                    # Server is still in the DNS
                    if ip_addr in records:

                        # Server is the last in the DNS
                        if len(records) < 2:
                            logger.error('[ERROR] Server {0} seems dead and '
                                         'it is on a DNS record for {1}, but '
                                         'it will not be removed since it is '
                                         'the last server.'
                                         .format(ip_addr, fqdn))

                        # Server is not the last. Delete it.
                        else:
                            logger.error('[ERROR] Server {0} seems dead and '
                                         'it is on a DNS record for {1}. '
                                         'Removing it.'
                                         .format(ip_addr, fqdn))
                            try:
                                n_deleted = dns.delete_a_record(fqdn, ip_addr)
                            except Exception as e:
                                logger.error('[ERROR] Error while deleting '
                                             'record {0} for {1}: {2}'
                                             .format(ip_addr, fqdn, e))
                            else:
                                logger.info('[INFO] Records targeting {0} '
                                            'were removed from the DNS ({1}).'
                                            .format(ip_addr, n_deleted))
                                # Only remove one server at a time
                                break

                    # Server not in the DNS
                    else:
                        logger.info('[INFO] Server {0} continues dead.'
                                    .format(ip_addr))

                # Server seems alive
                else:

                    # Server is already in the DNS
                    if ip_addr in records:
                        logger.info('[INFO] Server {0} seems alive and it is '
                                    'on the DNS'
                                    .format(ip_addr))

                    # Server is not in the DNS. Add it.
                    else:
                        logger.warning('[WARNING] Server {0} seems alive and '
                                       'it is not on a DNS record for {1}. '
                                       'Adding it.'
                                       .format(ip_addr, fqdn))
                        try:
                            dns.add_a_record(fqdn, ip_addr)
                        except Exception as e:
                            logger.error('[ERROR] Error while adding record '
                                         '{0} for {1}: {2}'
                                         .format(ip_addr, fqdn, e))
                        else:
                            logger.info('[INFO] Record targeting {0} was '
                                        'added to the DNS.'
                                        .format(ip_addr))
