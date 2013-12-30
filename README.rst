===============================
Python DNS Failover
===============================

.. image:: https://badge.fury.io/py/python-dns-failover.png
    :target: http://badge.fury.io/py/python-dns-failover
    
.. image:: https://travis-ci.org/marccerrato/python-dns-failover.png?branch=master
        :target: https://travis-ci.org/marccerrato/python-dns-failover

.. image:: https://pypip.in/d/python-dns-failover/badge.png
        :target: https://crate.io/packages/python-dns-failover?version=latest


Python script to automatically update DNS records for a bunch of servers participating in a Round-Robin DNS setup.

* Free software: BSD license
* Documentation: http://python-dns-failover.rtfd.org.

This project is mainly based on `@dotcloud`_'s work on his project `autodnsfailover`_.

The main difference is that **python-dns-failover** script is aimed to **run in an external
machine** while `autodnsfailover`_ is to run in the participating servers themselves.

.. _`@dotcloud`: https://github.com/dotcloud/
.. _`autodnsfailover`: https://github.com/dotcloud/autodnsfailover

DNS Backends
----------------
A DNS backend is responsible for updating the DNS records. It must provide the following methods:

* **get_a_records(fqdn)**: Returns the list of ip adresses records associated with the given FQDN.
* **add_a_record(fqdn, ip)**: Adds a resource record of type A to the DNS list. Optionally return the new record created.
* **delete_a_record(fqdn, ip)**: Deletes all DNS A-type resource records targeting the given ip. Optionally return the number of deleted records.

The constructor will typically be implementation-dependent, and allow to set the credentials and/or the zone to act upon.

Available DNS Backends
~~~~~~~~~~~~~~~~~~~~~~~
* `CloudFlareDNS`_
	- `email`: E-mail address of your CloudFlare account.
	- `key`: API key of your CloudFlare account.
	- `zone`: target DNS full qualified domain name.
	- `ttl`: TTL of record in seconds. 1 = Automatic, otherwise, value must in between 120 and 4,294,967,295 seconds. Defaults to 1.
	- `url`: CloudFlare client gateway interface url. Defaults to 'https://www.cloudflare.com/api_json.html'.

.. _`CloudFlareDNS`: http://www.cloudflare.com/

TODO
--------
* Documentation
* Testing