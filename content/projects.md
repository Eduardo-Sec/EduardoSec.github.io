---
title: Projects
type: page
layout: projects
draft: false
projects:
  - title: Proxmox home lab
    status: in progress
    status_type: warn
    tags: [proxmox, pfsense, wazuh, detection]
    desc: Dedicated security lab on a mini PC running Proxmox. pfSense for WAN/LAN separation, Wazuh for log collection, isolated malware sandbox, and QEMU ARM environment.

  - title: ARM malware analysis
    status: in progress
    status_type: warn
    tags: [ghidra, qemu, arm, wazuh]
    desc: Static and dynamic analysis environment for ARM binaries. Starting with Mirai variants, ending with paired writeup and Wazuh detection rules built from real behavioral findings.

  - title: Portfolio site
    status: in progress
    status_type: warn
    tags: [hugo, github-pages, css]
    desc: This site. Custom Hugo theme from scratch, deployed on GitHub Pages. Planning migration to self-hosted Proxmox with Cloudflare tunnel once the lab is up.
    url: https://github.com/Eduardo-Sec/EduardoSec.github.io

  - title: Security+
    status: exam scheduled summer 2026
    status_type: info
    tags: [SY0-701, certifications, blue team]
    desc: Working through SY0-701 with focus on Domain 4. After Security+, CySA+ is next since it maps directly to detection engineering work.
---

These are things I am actively working on. Nothing here is listed as finished until it actually is.

## Proxmox home lab

**Status: in progress, waiting on hardware**

Building a dedicated security lab on a Bosgame P3 Lite mini PC running Proxmox. The plan is to run pfSense on the dual 2.5GbE NICs for real WAN/LAN separation, a Wazuh server to collect logs from all lab VMs, a Kali attack machine, an isolated Windows sandbox for malware analysis, and a Ubuntu target with a QEMU ARM environment for low-level work.

The goal is to have a self-contained detection engineering pipeline running on my own hardware rather than relying on cloud labs or single-VM setups. Once it's running I'll be documenting the setup and writing up detection use cases built from real traffic generated inside the lab.

## ARM malware analysis environment

**Status: in progress**

Setting up a local environment for static and dynamic analysis of ARM architecture binaries. This means Ghidra with ARM processor support on my desktop and QEMU for emulation on the lab machine once the hardware arrives.

The starting point is Mirai botnet variants since they are ARM-compiled, well-documented, and still active in the wild. The end goal is a paired analysis writeup and set of Wazuh detection rules built from actual behavioral findings, not just pulled from public threat intel.

This is a longer-term project that will run alongside my Malware Analysis course in fall 2027.

## Portfolio site

**Status: in progress**

This site. Built with Hugo and a custom theme from scratch. Deployed on GitHub Pages and pointed at a personal domain. No templates, no page builders, just HTML, CSS, and Hugo templating.

The plan is to migrate to self-hosted on the Proxmox lab once that is up and running, using a Cloudflare tunnel for public access without exposing a home IP.

Source is on GitHub if you want to look at how it is put together.

## Security+

**Status: in progress, exam scheduled for summer 2026**

Working through the SY0-701 objectives with a focus on Domain 4 since Security Operations is the heaviest weighted section and maps most directly to the detection engineering work I do day to day. Using Professor Messer videos and Jason Dion practice exams.

After Security+ the plan is CySA+ since it is the blue team cert that aligns most directly with where I want to take my career.
