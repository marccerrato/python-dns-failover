#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dns_failover
import logging
import logging.handlers
import os

# DNS name used by the round-robin setup
fqdn = 'sub.example.com'

# IP addresses used by the round-robin setup
ip_addresses = ['1:2:3:4', '5:6:7:8', '9:10:11:12']

# CloudFlare DNS configuration
cloudflare_email = os.getenv('CLOUDFLARE_EMAIL', 'sample@example.com')
cloudflare_key = os.getenv('CLOUDFLARE_API_KEY', '8afbe6dea02407989af4dd4c97bb6e25')
cloudflare_zone = 'example.com'

# Implementation to be used to update the DNS records
dns = dns_failover.backends.CloudFlareDNS(
    email=cloudflare_email,
    key=cloudflare_key,
    zone=cloudflare_zone,
)

# Implementation to be used to check if a server is alive
check = dns_failover.HttpCheck()

# Implementation to be used for timing parameters (how often to run the checks)
timer = dns_failover.TickTimer(interval=300, timeout=3, retry=5)

# Logger to use
logger = logging.getLogger('dns_failover')
logger.setLevel(logging.DEBUG)

# Add console handler to tollger
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# Email configuration w/ Gmail
email_from_addr = os.getenv('EMAIL_FROM_ADDR', 'DNS Failover <from@example.com>')
email_to_addr = os.getenv('EMAIL_TO_ADDR', ['to1@example.com', 'to2@example.com'])
email_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
email_port = os.getenv('EMAIL_PORT', 587)
email_host_user = os.getenv('EMAIL_HOST_USER', 'from@example.com')
email_host_password = os.getenv('EMAIL_HOST_PASSWORD', 'Password123456')
email_use_tls = os.getenv('EMAIL_USE_TLS', True)
email_subject = os.getenv('EMAIL_SUBJECT', "DNS Failover Log")

# Add email handler to logger
email_handler = logging.handlers.SMTPHandler(
    mailhost=(email_host, email_port),
    fromaddr=email_from_addr,
    toaddrs=email_to_addr,
    subject=email_subject,
    credentials=(email_host_user, email_host_password),
    secure=() if email_use_tls else None,
)
email_handler.setLevel(logging.WARNING)
logger.addHandler(email_handler)

# Run the DNS updater with all the previously set parameters!
dns_failover.run(fqdn, ip_addresses, dns, check, timer, logger)
