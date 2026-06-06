---
title: "Hardening the home lab network, VLANs, DNS blocking, and pfSense security configuration"
date: 2026-06-05
tags: ["project"]
draft: false
---

## Overview

This picks up where the first writeup left off. The network was online with pfSense routing, pfBlockerNG doing basic DNS blocking, and the EAP673 broadcasting a single SSID. This session covers the next layer, network segmentation with VLANs, expanded DNS blocking with over 1.29 million entries, DNS over TLS, firewall hardening, and a handful of stability improvements specific to running pfSense as a Proxmox VM. Software versions reflect the build at time of writing and may have been updated since.

---

## VLAN design

I wanted three isolated network segments sharing the same physical hardware. The main LAN at 10.10.10.0/24 for trusted devices, an IoT VLAN at 10.10.20.0/24 for phones and smart devices, and a Guest VLAN at 10.10.30.0/24 for visitors. The reasoning behind putting personal phones on the IoT VLAN rather than the main LAN is that phones have dozens of apps with unknown behavior and no legitimate reason to reach lab infrastructure. Keeping them alongside the Roku also means casting still works since those devices can see each other on the same segment.

The physical setup required no switch reconfiguration. The UGREEN switch in Standard mode passes 802.1Q tagged frames through without modification. The actual VLAN work happens entirely in pfSense and the EAP673, which is the correct place for it.

---

## pfSense VLAN configuration

I created two VLAN interfaces in pfSense under Interfaces, Assignments, VLANs with vtnet0 as the parent interface, VLAN tag 20 for IoT and VLAN tag 30 for Guest. After assigning both as interfaces and enabling them with static IPs of 10.10.20.1/24 and 10.10.30.1/24, I set up DHCP on each with ranges 10.10.20.100 to 10.10.20.199 and 10.10.30.100 to 10.10.30.199.

The firewall rules on each VLAN tab are order-dependent since pfSense evaluates top to bottom and stops at the first match. The IoT rules in order are Block IoT to LAN, Block IoT to Guest, Allow IoT internet. The Guest rules are Block Guest to LAN, Block Guest to IoT, Allow Guest internet. The block rules must sit above the pass rule or the pass rule fires first and the blocks never execute.

I verified isolation by connecting a phone to each SSID and confirming it got the correct subnet IP, could browse the internet, and could not reach 10.10.10.1 or the other VLAN gateways.

---

## AP SSID configuration

The EAP673 required two new SSIDs in the Omada app, one for each VLAN. The IoT SSID uses WPA2/WPA3 mixed mode with VLAN ID 20 tagged, and guest network isolation left off so phones and the Roku can communicate for casting. The Guest SSID uses WPA2/WPA3 with VLAN ID 30 tagged and client isolation enabled so guest devices cannot see each other. The main Lab SSID remains untagged, flowing to the main LAN naturally.

When the AP tags traffic with a VLAN ID, the frames reach nic1 on the P3 Lite, enter vmbr0, and pfSense sees the 802.1Q tag and routes the traffic to the appropriate interface. One physical cable from the switch to the AP carries all three networks simultaneously.

---

## Expanding pfBlockerNG

The initial pfBlockerNG setup from the first session loaded the default wizard feeds. I expanded this significantly by adding feeds through the DNSBL Groups configuration.

OISD was the first addition I attempted. It returned a 410 Gone error because OISD discontinued hosts and domains syntax support in 2024 and pfBlockerNG's current wildcard implementation is not compatible with their remaining formats. The replacement was Hagezi Pro Plus, a compilation blocklist specifically maintained for pfBlockerNG compatibility, loaded via the Hagezi DNS blocklists CDN. It came in at 545,521 entries after deduplication.

The IPv6 DNSBL VIP was also missing from the initial setup, which caused DNSBL to be globally disabled despite appearing configured. The fix was creating a VIP for ::1/128 on the localhost interface under Firewall, Virtual IPs and selecting it in the pfBlockerNG DNSBL settings. Without this the entire DNSBL system silently does nothing.

Additional feeds enabled after getting DNSBL working were StevenBlack unified hosts, AdGuard DNS, Hagezi Pro Plus, Phishing Army, Frogeye first and multi-party trackers, Lightswitch05, DandelionSprouts anti-malware, Prigent malware, URLhaus, Microsoft telemetry, Roku and Android specific tracker lists, EasyList, and EasyPrivacy. The final count landed at 1,295,242 blocked domains across all active lists.

---

## DNS over TLS

I enabled DNS query forwarding in the Unbound resolver under Services, DNS Resolver, General Settings and checked both Enable Forwarding Mode and Use SSL/TLS for outgoing DNS Queries to Forwarding Servers. The upstream DNS servers in System, General Setup are Cloudflare at 1.1.1.1 and 1.0.0.1 and Quad9 at 9.9.9.9, all with their TLS hostnames configured for certificate verification. Cloudflare uses one.one.one.one and Quad9 uses dns.quad9.net.

All DNS queries leaving the network now travel encrypted over port 853. This prevents the ISP from seeing which domains any device on the network resolves. pfBlockerNG continues intercepting blocked domains before they reach the upstream servers since Unbound processes the query first.

---

## DNS bypass blocking

Without explicit firewall rules, a device like a Roku can hardcode 8.8.8.8 as its DNS server and bypass pfBlockerNG entirely. I added two rules to both the IoT and Guest firewall tabs to close this. The first is a pass rule allowing DNS traffic from the VLAN subnet to the pfSense interface address on that VLAN, and the second is a block rule dropping all other DNS traffic to any destination. This forces every device to use pfSense for DNS resolution regardless of what the device wants to use.

---

## Proxmox VM stability fixes

Running pfSense as a Proxmox VM with VirtIO NICs requires a few specific settings that are not obvious from the pfSense documentation.

Disabling hardware checksum offloading, TCP segmentation offloading, and large receive offloading under System, Advanced, Networking prevents packet corruption issues that appear intermittently with VirtIO. These options offload network processing to hardware that does not exist in a virtualized environment, causing occasional dropped or malformed packets.

Setting the firewall optimization to Conservative under System, Advanced, Firewall and NAT keeps state table entries alive longer. This is better suited to a lab environment where connections come and go frequently and short timeouts cause premature state expiration.

---

## PHP memory issue with large DNSBL

Loading 1.29 million domains into Unbound's database creates a memory pressure problem. The kea2unbound script, which synchronizes Kea DHCP static mappings to Unbound's DNS resolver, was consistently hitting the default PHP memory limit of 512 megabytes and crashing. The crash appeared in the dashboard as a PHP fatal error in kea2unbound at line 524 and repeated every time a DHCP config change triggered the sync.

The fix required creating a PHP configuration override rather than using pfSense's System Tunables, which only affect the web interface PHP process and not CLI scripts. I created /usr/local/etc/php.ini.d/ and added a memory.ini file setting memory_limit to 1024M. This required restarting php-fpm with /usr/local/etc/rc.d/php-fpm onerestart afterward.

---

## Static DHCP mappings and lease times

I added static DHCP mappings for my laptop's Ethernet and WiFi adapters under Services, DHCP Server, LAN with static ARP entries enabled, assigning each a fixed IP in the 10.10.10.x range. This ensures the laptop always gets the same IP regardless of which adapter is active.

The default DHCP lease time of 7200 seconds, two hours, caused frequent renewals that could produce brief connectivity interruptions. I changed the default lease time to 86400 seconds and the maximum to 604800 seconds across all three VLAN DHCP servers.

---

## Additional hardening

I moved the pfSense web UI from port 443 to port 4443 under System, Advanced, Admin Access to reduce automated scan exposure. UPnP was confirmed disabled under Services, UPnP IGD and PCP, blocking IoT devices from autonomously opening ports through the firewall. BOGON and RFC1918 blocking were confirmed enabled on the WAN interface. The DHCP backend was switched from ISC DHCP to Kea following pfSense's end-of-life notice for ISC DHCP.

---

## What is deferred

Suricata as a pfSense IDS/IPS package is the next pfSense addition. Running it on the WAN and LAN interfaces feeds network-level alerts into Wazuh once that VM is running, creating correlated host and network detection.

The Mullvad VPN setup over WireGuard is next in the privacy queue. Running pfSense as a VPN client means all traffic from every device routes through the tunnel automatically without configuring anything per device. This is particularly relevant for the lab work since malware analysis and threat research should not originate from a residential Cox IP.

Wazuh is the immediate next session priority. Everything built here, the VLANs, the DNS blocking, the firewall rules, all of it becomes more useful once there is a SIEM ingesting logs and generating alerts from the network activity.
