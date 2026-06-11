---
title: "Building the home lab, Proxmox, pfSense, and a production-grade home network from scratch"
date: 2026-06-04
tags: ["project"]
draft: false
---

## Overview

I built this to have a dedicated platform for detection engineering work outside of my internship, somewhere to run Wazuh, test detection rules, and work through malware analysis without touching production systems. I wanted the network layer to be real infrastructure rather than a consumer router, which meant pfSense on a hypervisor instead of anything off the shelf.

The hardware is a BOSGAME P3 Lite mini PC running a Ryzen 7 6800H with 32GB DDR5 and dual 2.5GbE ports. It runs Proxmox VE 9.2 as the hypervisor with pfSense CE 2.8 as a VM handling all routing and firewalling. The rest of the physical stack is a Hitron CODA56 DOCSIS 3.1 modem, a UGREEN 10-port PoE switch, and a TP-Link EAP673 access point running in AP mode powered via PoE from the switch. ISP is Cox 1 Gig with unlimited data. Software versions reflect the build at time of writing and may have been updated since.

I document the failures as thoroughly as the decisions that worked here because most of the useful information is in the troubleshooting, not the happy path.

---

## Hardware and ISP decisions

I picked the P3 Lite specifically for the dual 2.5GbE ports. A soft router with only gigabit NICs works fine for a 1 Gig ISP plan but leaves no headroom if speeds increase or if internal traffic between VMs and physical devices ever needs to move faster than 1 Gbps. The 2.5GbE ports meant the WAN and LAN boundaries could handle more than the ISP connection without becoming a bottleneck.

Fiber was not available at my address despite being in Omaha. Cox cable was the only real option. I went with the 1 Gig plan with unlimited data to avoid data cap concerns, which matters because VM image downloads, OS updates across multiple machines, and general lab traffic adds up faster than expected.

The modem situation had a detour. I originally ordered an ARRIS S33, which has a 2.5GbE port matching the P3 Lite's WAN NIC. Cox's activation portal rejected it and a support agent confirmed it was no longer supported on their network. I swapped it for the Hitron CODA56, a standalone DOCSIS 3.1 modem on Cox's certified list for up to 2 Gig, also with a 2.5GbE port.

I chose 10.10.10.0/24 as the LAN subnet deliberately rather than using the default 192.168.1.0/24 or 192.168.0.0/24. Those ranges conflict with the most common home network subnets and cause routing problems when connected to a work VPN that uses the same range. The 10.10.10.x space is uncommon enough in external networks to avoid that problem.

---

## Proxmox installation

The P3 Lite ships with Windows. I installed Proxmox by booting from a USB drive flashed with the Proxmox VE ISO. Before booting the installer I checked that SVM mode was enabled in the BIOS. It was already on by default on this hardware but skipping that check on a fresh machine is the kind of thing that causes confusing failures later since VMs simply will not run without it.

The P3 Lite's network interfaces have unusual naming in Proxmox worth documenting. The two physical 2.5GbE NICs show up as nic0 and nic1 in the Proxmox network interface list, with alternative names following the enx prefix and MAC address pattern rather than the standard enp PCI path naming. This matters when creating Linux bridges manually because specifying the altname in the bridge configuration fails with an "unable to find bridge port" error. The correct value to use is the primary interface name, nic0 or nic1.

I set the management IP to 10.10.10.10/24 with nic1 as the LAN bridge port on vmbr0. I created a second bridge, vmbr1, on nic0 for the WAN side connecting to the modem. This bridge has no IP assigned on the Proxmox host since pfSense handles all addressing on the WAN interface.

The Proxmox installer defaults to the enterprise package repository which requires a paid subscription. On first login I switched it to the no-subscription repository under the node's Updates section and disabled the enterprise Ceph repository since it is not relevant to a single-node setup.

---

## pfSense VM creation

I built the pfSense VM with 2 vCPUs, 2GB RAM, a 32GB VirtIO disk on local-lvm, and two VirtIO network interfaces, net0 on vmbr0 as LAN and net1 on vmbr1 as WAN. I set the CPU type to host to pass through the actual processor features including AES-NI, which pfSense uses for VPN and encryption.

The installer I used was the Netgate universal installer ISO for AMD64 virtual machines. This turned out to be a pfSense Plus installer rather than a standalone pfSense CE ISO, and it requires an active internet connection during installation to reach Netgate's servers for license validation. That requirement was not obvious from the download page and caused the first three installation attempts to fail at the connectivity check step with no internet connected to the WAN interface.

Getting the WAN online during installation required cycling through a few issues. The first problem was that running dhclient on vmbr1 from the Proxmox host to test Cox connectivity grabbed the DHCP lease on Proxmox's MAC address. When pfSense's installer then tried to get its own DHCP lease from Cox, Cox's CMTS had already bound the lease to the Proxmox host MAC and rejected the pfSense VM's different MAC. Power cycling the modem cleared the binding and let pfSense's vtnet1 get the Cox IP on the next installation attempt.

The installer then offered the option to install pfSense CE instead of validating a Plus subscription, which is the correct path for a home lab. pfSense CE installed cleanly after that.

---

## The LAN interface problem

After the first boot into the installed pfSense, the network did not come up. Devices on the LAN got no DHCP responses and the pfSense console showed only the WAN interface assigned with no LAN. The LAN interface assignment had not been saved properly during the installation wizard despite the installer showing it as configured.

Diagnosing this without working internet on the laptop meant working entirely from the Proxmox physical console. I confirmed the tap interfaces for the pfSense VM were active on the correct bridges using ip link show filtered for tap, ran tcpdump on vmbr0 to see what traffic was actually present on the LAN bridge, and checked the routing table to understand why pings to expected pfSense IPs were failing.

The tcpdump results on vmbr0 showed only the laptop's self-assigned APIPA traffic at 169.254.x.x with no traffic from pfSense at all. Pinging 192.168.1.1 failed not because pfSense was absent but because Proxmox's management IP of 10.10.10.10 was on a different subnet with no route, so the ICMP unreachable responses never came back even if pfSense had been there.

Getting the laptop internet access back required a temporary workaround. With pfSense stopped, I ran dhclient on vmbr1 to get the Cox IP, enabled IP forwarding on the Proxmox host, added an iptables NAT masquerade rule routing LAN traffic out through vmbr1, and corrected the default route to point at the Cox gateway on vmbr1 rather than the nonexistent pfSense LAN gateway. This gave the laptop enough connectivity to reach the Proxmox web UI and access the pfSense VM console via noVNC.

From the pfSense console I used option 1 to assign interfaces and added vtnet0 as LAN, then option 2 to set the LAN IPv4 address to 10.10.10.1/24 with DHCP enabled on the range 10.10.10.100 to 10.10.10.199. Once pfSense came back up with a working LAN, I removed the temporary Proxmox NAT and corrected the default route to 10.10.10.1 on vmbr0.

---

## Access point setup

The EAP673 connects to the UGREEN switch via a single Cat6A cable on any port from 1 to 8. The switch provides PoE power over that cable so the AP needs no separate power supply. It picked up a DHCP address from pfSense automatically on boot.

The Omada app on mobile discovers the AP on the local network and handles the initial setup wizard. Setting up the primary SSID and password took under five minutes. I configured the AP in access point mode rather than router mode, meaning pfSense handles all DHCP, DNS, and routing while the EAP673 handles only the wireless layer. Running it as a router would create double NAT between pfSense and wireless clients, which is the wrong topology here.

---

## pfBlockerNG

I installed pfBlockerNG-devel from the pfSense package manager under System, Package Manager, Available Packages. The devel version is the actively maintained branch and the better choice over the standard release.

The setup wizard prompts for a DNSBL Virtual IP, which requires creating a VIP on the localhost interface under Firewall, Virtual IPs first. My first attempt used 10.10.10.2/32, which failed validation because pfSense flagged it as overlapping with the existing 10.10.10.0/24 LAN subnet even though it was on the localhost interface. I used 172.16.0.1/32 from the RFC 1918 172.16.0.0/12 range instead since it has no overlap with any configured network.

The wizard completed with over 159,000 entries loaded across IP and DNSBL blocklists covering Abuse Feodo, Emerging Threats, Spamhaus DROP, CINS Army, and ISC block feeds. DNS-based blocking is active for all devices on the network using pfSense as their resolver, which they receive automatically via DHCP.

DNS blocking does not affect YouTube ads. Google serves ads from the same domains as video content, making DNS-level differentiation impossible. Browser extensions are the only reliable solution for that specific case.

---

## Serial console access

I added a serial interface to the pfSense VM to enable console access from the Proxmox shell without needing the web UI. The command is `qm set 100 -serial0 socket` followed by stopping and starting the VM. After that `qm terminal 100` connects to the pfSense console directly from the Proxmox command line. This turned out to be essential during the period when the laptop had no network access and the Proxmox web UI was unreachable.

---

## Auto-start configuration

I set the pfSense VM to start automatically when Proxmox boots with `qm set 100 --onboot 1`. Without this a Proxmox reboot for kernel updates leaves the network down until the VM is started manually.

---

## What is deferred

VLAN segmentation for IoT devices and a guest network is the next configuration priority. I want to isolate untrusted devices on a separate VLAN with a firewall rule allowing internet access but blocking access to the 10.10.10.0/24 segment, so a compromised or aggressively tracking device cannot reach lab infrastructure.

Suricata as a pfSense IDS/IPS package, Wazuh as the primary SIEM VM, and a Windows malware sandbox are the next lab VM additions. Wazuh takes priority since it ties directly to detection engineering work at my internship and gives me a home environment to build and test detection rules without affecting production.

The portfolio site migration from GitHub Pages to self-hosted Django and Nginx with a Cloudflare tunnel becomes more relevant now that the infrastructure to host it is running. That migration also unblocks the security headers currently deferred due to GitHub Pages limitations.
