#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests


class CloudFlareDNS(object):
    """
    CloudFlare Backend for Python DNS Failover
    """

    def __init__(self, email, key, zone, ttl=1,
                 url='https://www.cloudflare.com/api_json.html'):
        """
        Sets up a CloudFlareDNS backend instance with the provided
        configuration.

        # Params:

        - `email`: E-mail address of your CloudFlare account.
        - `key`: API key of your CloudFlare account.
        - `zone`: DNS target full qualified domain name.
        - `ttl`: TTL of record in seconds. 1 = Automatic, otherwise, value
                 must in between 120 and 4,294,967,295 seconds.
        - `url`: CloudFlare client gateway interface url.
        """
        self.url = url
        self.zone = zone
        self.ttl = ttl

        self.base_data = {
            'email': email,
            'tkn': key,
            'z': self.zone,
        }

    def _do_request(self, data={}):
        """
        Configures and does the request to the backend API endpoint
        and catches any possible exception.

        # Params:

        - `data`: additional data for the request.
        """
        data.update(self.base_data)

        response = requests.post(self.url, data=data)
        response.raise_for_status()
        response_data = response.json()

        # If result is not successful, raise error
        if response_data.get('result') != 'success':
            raise Exception(response_data.get('msg'))

        return response_data

    def _hostname(self, fqdn):
        """
        Asserts that the given FQDN belong to the configured zone and
        returns the hostname.

        # Params:

        - `fqdn`: full qualified domain name to retrieve the hostname from.
        """
        zone = '.' + self.zone
        assert fqdn.endswith(zone)
        return fqdn[:-len(zone)]

    @property
    def _records(self):
        """
        Load all current DNS zone records.
        Returns the list of the current DNS zone records.
        """
        data = {
            'a': 'rec_load_all',
        }
        response = self._do_request(data=data)
        return response.get('response').get('recs').get('objs')

    def get_a_records(self, fqdn):
        """
        Returns the list of ip adresses records associated with the given FQDN.

        # Params:

        - `fqdn`: full qualified domain name of the records to retrieve.
        """
        return [record.get('content')
                for record in self._records
                if record.get('name') == fqdn and record.get('type') == 'A']

    def add_a_record(self, fqdn, ip):
        """
        Adds a resource record of type A to the DNS list.
        Returns the new record created.

        # Params:

        - `fqdn`: full qualified domain name to add to the dns record.
        - `ip`: server ip to add to the dns record.
        """

        data = {
            'a': 'rec_new',
            'content': ip,
            'name': self._hostname(fqdn),
            'ttl': self.ttl,
            'type': 'A',
        }
        response = self._do_request(data=data)
        new_record = response.get('response').get('rec').get('obj')

        return new_record

    def delete_a_record(self, fqdn, ip):
        """
        Deletes all DNS A-type resource records targeting the given ip.
        Returns the number of deleted records.

        # Params:

        - `fqdn`: full qualified domain name of the dns record to remove.
        - `ip`: target ip to remove from the dns record to remove.
        """
        num_deleted = 0
        for record in self._records:
            if record.get('name') == fqdn and \
               record.get('type') == 'A' and \
               record.get('content') == ip:
                data = {
                    'a': 'rec_delete',
                    'id': record.get('rec_id'),
                }
                self._do_request(data=data)
                num_deleted += 1

        return num_deleted
