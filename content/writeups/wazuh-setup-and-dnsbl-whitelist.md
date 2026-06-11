---
title: "Deploying and hardening Wazuh, SIEM setup, pfSense integration, and custom detection rules"
date: 2026-06-11
tags: ["project"]
draft: false
---

## Overview

This picks up where the network hardening writeup left off. pfSense was fully configured with VLAN segmentation, DNS blocking, and syslog forwarding pre-aimed at an IP that did not exist yet. This session covers standing up the Wazuh SIEM, hardening the VM before writing a single rule, integrating pfSense as a log source, resolving streaming service conflicts with the DNS blocklist, writing the first custom detection rules, and getting everything visible in the dashboard. Software versions reflect the build at time of writing and may have been updated since.

-----

## VM provisioning

The Wazuh VM runs Ubuntu 26.04 LTS on Proxmox with VM ID 101. The hardware allocation is 2 vCPUs, 4 GB RAM, and a 100 GB VirtIO disk on local-lvm. The network interface is VirtIO on vmbr0, the same bridge pfSense’s LAN side sits on, placing the Wazuh VM at 10.10.10.50/24 with pfSense at 10.10.10.1 as the gateway.

One thing worth documenting for anyone running Wazuh on Ubuntu 26.04 is that the installer flags it as unsupported since Wazuh’s recommended list stops at 22.04. The installer proceeds fine with the -i flag to skip the hardware check. The hardware check itself was also relevant since 4 GB at install time leaves the Java-based indexer competing with the OS for memory. The warning is legitimate but the deployment runs stably at this allocation for a lab environment with light traffic.

VirtIO NIC stability on Proxmox required running ethtool on the host to disable hardware checksum offloading and TSO on vmbr0. This is the same fix applied to the pfSense VM in the previous session. Without it VirtIO NICs on Proxmox exhibit intermittent packet corruption.

-----

## Wazuh installation

The all-in-one installer handles the indexer, manager, and dashboard in a single run. I pulled the 4.11 installer and config.yml directly from the Wazuh package server, edited config.yml to set all node IPs to 10.10.10.50, and ran the installer. It generated TLS certificates, initialized the indexer cluster, started all four services, and printed credentials at the end. The credentials are only displayed once and are not recoverable without resetting the indexer, so copying them immediately matters.

After the install the four services all came up clean. The indexer is the heaviest, running a Java heap that routinely uses swap on a 4 GB VM. This is expected behavior at this RAM allocation and does not affect functionality for lab-scale traffic.

I moved the dashboard from the default port 443 to 5443 for consistency with how the pfSense web UI is on a non-default port. The change is a single line in /etc/wazuh-dashboard/opensearch_dashboards.yml.

-----

## Hardening

I ran through a full hardening pass before touching any detection configuration. The sequence was SSH, firewall, service accounts, file permissions, and auditd.

SSH hardening started with generating an ed25519 key pair and copying the public key to the VM. After confirming key authentication worked I set PasswordAuthentication to no, PermitRootLogin to no, MaxAuthTries to 3, and AllowUsers to my account, then reloaded sshd. Testing from a new terminal before closing the original session is the only safe way to do this since a misconfiguration that locks you out requires console access through Proxmox to recover.

The UFW firewall defaults to deny incoming and allow outgoing. I added allow rules scoped to 10.10.10.0/24 for SSH on 22, the dashboard on 5443, agent log forwarding on UDP 1514, agent enrollment on 1515, the Wazuh API on 55000, and syslog on UDP 514. Scoping all rules to the LAN subnet means none of these ports are reachable from the IoT or Guest VLANs without a deliberate firewall change.

The service account situation required creating a dedicated filebeat user since Filebeat on Ubuntu does not create one by default and runs as root out of the box. I created a system account with no login shell, changed ownership on /var/lib/filebeat, /var/log/filebeat, and /usr/share/filebeat to that account, added the filebeat user to the wazuh group so it could traverse the log directory hierarchy, edited the systemd service file to specify User and Group, and reloaded the daemon. Confirming the process runs as filebeat rather than root via ps aux is the verification step that matters here.

The wazuh and wazuh-indexer accounts were already set to nologin shells by the installer. The wazuh-dashboard account used /bin/false, which is functionally equivalent.

File permissions were tightened on /var/ossec/etc, /etc/filebeat, and the certificate directories for both the indexer and dashboard, setting directories to 750 and files to 640 or 600 depending on whether they need to be readable by group members.

Auditd monitors the Wazuh configuration files themselves, the SSH config, sudoers, and the auth log. The rules use the -w watch flag with -p wa for write and attribute change events, and -k key tags for easy filtering. The most useful rules for this environment are the ones watching /var/ossec/etc/ossec.conf and /var/ossec/etc/rules since any modification to detection logic should be visible as an audit event.

-----

## Socket buffer fix

After the Wazuh manager started, the syslog remote listener bound to UDP 514 correctly but received zero bytes even with packets confirmed arriving at the NIC via tcpdump. The root cause was the kernel default socket receive buffer being too small for the rate of incoming syslog traffic from pfSense. Adding net.core.rmem_max and net.core.rmem_default at 26214400 to /etc/sysctl.conf and applying them immediately with sysctl -w resolved it. A single test packet to the listener confirmed the fix by incrementing the analysisd total_events_decoded counter.

-----

## pfSense syslog integration

pfSense had syslog forwarding pre-configured to 10.10.10.50 from the previous session. After the socket buffer fix, packets started flowing immediately. The syslog source on pfSense is bound to the LAN interface, forwarding Everything to the Wazuh IP on the default UDP 514 port.

One recurring issue was pfSense’s syslogd stopping remote forwarding after configuration saves. The syslog daemon restarts on config changes and does not always re-establish the remote connection. A cron job running every five minutes with killall -HUP syslogd keeps it alive without a full restart.

The remote listener block in ossec.conf specifies syslog connection type, UDP 514, and allows traffic from 10.10.10.0/24. Wazuh has a built-in pf decoder that parses pfSense filterlog entries when the syslog message arrives with a proper hostname field. The complication in this setup is that pfSense CE omits the hostname from filterlog syslog headers, sending filterlog[PID]: as the hostname field instead of the device hostname. This causes the Wazuh predecoder to misparse the message and the pf decoder to not fire.

The fix was a custom decoder in /var/ossec/etc/decoders/local_decoder.xml using a prematch on the string filterlog. With the predecoder failing to extract a program_name, the custom decoder matches on the raw log content and assigns the pfsense-filterlog decoder name, which is what the rule matching uses. Wazuh’s logtest tool confirmed all three phases completing correctly before testing against live traffic.

-----

## pfBlockerNG whitelist for streaming devices

After the Wazuh deployment I noticed Paramount+ was failing to load on devices on the IoT VLAN. The pfBlockerNG DNSBL report showed the root cause, vod.pplus.paramount.tech being blocked by the Frogeye multiparty trackers list. This is the actual video delivery CDN endpoint, not a tracking domain, so blocking it prevents playback entirely.

The initial attempts to whitelist the domain through pfBlockerNG’s group-level Custom_List field did not work because that field adds to the blocklist rather than exempting from it. The correct mechanism is the DNSBL Whitelist field in the main pfBlockerNG DNSBL tab. Entries there get written into the suppression file that pfBlockerNG runs against its compiled blocklist using ggrep -vF during every reload. Adding domains with a leading dot treats them as wildcard matches covering all subdomains, which was necessary for cws.conviva.com since Paramount+ uses hash-prefixed subdomains for video quality monitoring that vary per session.

The suppression file approach handled the DNSBL blocklist entries, but CNAME inspection was still following DNS resolution chains and finding blocked intermediate domains. The solution was configuring Unbound views to apply pfBlockerNG’s DNSBL config selectively based on which device is making the query.

The Unbound custom options in the DNS Resolver create two views, bypass and dnsbl. The pfBlockerNG include directive sits only in the dnsbl view. Per-device access-control-view assignments map streaming device IPs to bypass and everything else on the IoT and main LAN subnets to dnsbl. Devices in bypass resolve DNS normally against the upstream resolvers without any blocklist applied. Devices in dnsbl get full pfBlockerNG filtering as before.

Static DHCP mappings were added for the streaming devices to ensure their IPs remain fixed, which is required for the Unbound view assignments to remain accurate after lease renewals. The TV required a static IP outside the DHCP pool range since the Kea backend rejects static mappings that overlap with the dynamic range.

-----

## Custom detection rules

With the decoder working I wrote four rules in /var/ossec/etc/rules/local_rules.xml. Rule 100001 is the base rule at level 3, matching any event decoded as pfsense-filterlog that contains the string match,block. Rules 100002, 100003, and 100004 are children of 100001 at level 10, triggering on specific destination port strings in the filterlog CSV for Telnet on port 23, MySQL on port 3306, and PostgreSQL on port 5432.

The level 10 threshold for the port-specific rules reflects that inbound connection attempts to database and management ports from external IPs are genuinely worth surfacing. The WAN-facing IP receives constant scanning traffic, and a connection attempt to port 5432 from a random IP is meaningfully different from generic TCP SYN floods that rule 100001 catches at level 3.

Testing against live traffic by watching the alerts log in real time while pfSense was actively forwarding confirmed rule 100001 firing within seconds of restarting the manager. The alerts include GeoIP enrichment on the source IPs, populated automatically by Wazuh’s built-in GeoIP database. Port scans from IPs geolocating to various countries, database probes, and generic SYN floods all generate alerts with source location data attached.

-----

## Dashboard and indexing

Filebeat ships both alerts and archives to the OpenSearch indexer. Archives logging required enabling logall and logall_json in the global section of ossec.conf and enabling the archives module in /etc/filebeat/filebeat.yml. The archives index wazuh-archives-4.x-* appeared in the indexer after creating the index pattern in Stack Management.

The archives index captures all decoded events regardless of whether a rule fires. This is useful for seeing pfSense nginx access logs, DNS events, and system syslog from pfSense that do not generate alerts but provide useful context during investigations. The alerts index wazuh-alerts-4.x-* captures only events that match a rule above the configured minimum level.

Filebeat needed the wazuh group membership fix before it could read the archives.json and alerts.json files, which live under /var/ossec/logs/ with directory permissions owned by the wazuh group. The error manifested as permission denied on the parent directory rather than on the files themselves, which pointed to the traversal permission gap rather than the file ownership.

-----

## Dashboard customization

The dashboard was switched to dark mode via Stack Management, Advanced Settings. Custom branding was applied through the opensearchDashboards.branding block in opensearch_dashboards.yml, which controls the header mark, loading logo, and application title. A CSS override appended to the legacy_dark_theme.css asset file applies the color palette from my portfolio site, replacing default orange and blue accents with purple at #a855f7 on near-black panel backgrounds matching my site’s –bg: #0f0f0f and –bg-card: #0d0d0d variables.

The header mark and loading logo were replaced with a custom SVG using the eb hexagon shield monogram. The mark image is served from the dashboard’s own static asset path, meaning no external dependency or CDN is involved. The applicationTitle was set to eb.dev, SOC.

-----

## What is deferred

The first Wazuh agent enrollment is next. The most useful immediate target is enrolling a Kali Linux VM once it is stood up, since generating attack traffic from Kali toward other lab VMs and watching it appear in Wazuh alerts is the core detection engineering workflow this whole build exists to support.

The pfSense filterlog decoder currently matches but does not extract structured fields from the filterlog CSV payload. A more complete decoder would pull out source IP, destination IP, protocol, and port as separate fields, enabling dashboard visualizations by source country, most-targeted port, and protocol distribution without writing separate rules for each. That structured parsing is the next iteration on the pfSense integration.

ARM malware analysis using QEMU and Ghidra, starting with Mirai variants, feeds directly into writing detection rules for the behaviors Mirai exhibits. Once the sandbox VM is running the pipeline is, detonate sample, observe behavior in Wazuh, write rule, verify rule fires on replay.