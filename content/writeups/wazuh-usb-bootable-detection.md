---
Title: "Detecting bootable USB media with Wazuh"
date: 2025-04-03
tag: "detection"
draft: false
---

Removable media is one of those threat vectors that gets underestimated. A USB drive sitting on a desk looks harmless, but it might contain a live Linux environment, a Windows installer, a forensic toolkit, or a persistence mechanism that bypasses the running OS entirely. Standard endpoint controls don't help much if someone boots from USB before your agent ever starts.

This writeup covers a Wazuh detection use case for identifying bootable USB media on Linux endpoints. The detection is heuristic, meaning it combines filesystem type, volume label patterns, and known boot artifact paths to make an informed judgment about whether a connected USB device is likely bootable. It won't catch everything, but it gives you visibility you wouldn't otherwise have.

One important constraint to understand upfront: Wazuh is a host-based tool. It only operates once the monitored OS and agent are running. That means this use case cannot stop a BIOS or UEFI boot decision, and it cannot prevent someone from booting into another OS before the agent loads. What it can do is detect the presence of bootable media while the monitored system is running and generate an alert for SOC review.

## The detection approach

Rather than relying on a single indicator, the detection script layers three types of checks.

**Filesystem type.** `iso9660` and `udf` are almost exclusively used by ISO-based boot media. `vfat` and `exfat` are common on EFI boot partitions. `ntfs` shows up on Windows installers.

**Volume labels.** Labels like `UEFI`, `TAILS`, `VENTOY`, `KALI`, `CCCOMA_` (the Windows installer label), and similar strings are strong signals that a partition contains installer or live media.

**Boot artifact paths.** If the first two checks don't catch it, the script mounts the partition read-only and looks for known bootloader files: EFI binaries, GRUB configs, Windows boot manager files, `isolinux`, `ldlinux.sys`, `live/filesystem.squashfs`, and others.

This layered approach gives reasonable coverage across Windows installers, Linux live media, and common rescue tools without depending on any single indicator that could be spoofed or absent.

## The detection script

Place this at `/var/ossec/active-response/bin/check_usb_bootable.sh` on the monitored Linux endpoint:

```bash
#!/bin/bash

TMPDIR="/tmp/wazuh-usb-check"
mkdir -p "$TMPDIR"

found=0

get_pair_value() {
  local line="$1"
  local key="$2"
  printf '%s\n' "$line" | sed -n "s/.*${key}=\"\\([^\"]*\\)\".*/\\1/p"
}

add_csv_unique() {
  local current="$1"
  local item="$2"
  [ -z "$item" ] && { printf '%s\n' "$current"; return; }
  case ",$current," in
    *,"$item",*) printf '%s\n' "$current" ;;
    *)
      if [ -n "$current" ]; then printf '%s,%s\n' "$current" "$item"
      else printf '%s\n' "$item"; fi ;;
  esac
}

for dev in $(lsblk -dn -o NAME,TRAN,TYPE | awk '$2=="usb" && $3=="disk" {print $1}'); do
  device_detected=0
  reasons=""
  labels=""

  while IFS= read -r line; do
    NAME="$(get_pair_value "$line" "NAME")"
    FSTYPE="$(get_pair_value "$line" "FSTYPE")"
    LABEL="$(get_pair_value "$line" "LABEL")"
    MOUNTPOINT="$(get_pair_value "$line" "MOUNTPOINT")"

    [ -z "$NAME" ] && continue
    [ "$NAME" = "$dev" ] && continue

    part="/dev/$NAME"
    bootable=0
    reason=""
    mnt="$MOUNTPOINT"
    mounted_here=0

    case "$FSTYPE" in
      iso9660|udf)
        bootable=1; reason="image_fs" ;;
      vfat|fat|exfat)
        if printf '%s\n' "$LABEL" | grep -Eiq \
          'TAILS|UEFI|EFI|VENTOY|LIVE|INSTALL|BOOT|CCCOMA_|ROCKY|UBUNTU|DEBIAN|KALI|FEDORA|RHEL|CENTOS|MINT|ARCH|MANJARO'; then
          bootable=1; reason="common_boot_label_matched"
        fi ;;
      ntfs)
        if printf '%s\n' "$LABEL" | grep -Eiq 'CCCOMA_|WIN|BOOT|INSTALL'; then
          bootable=1; reason="windows_boot_label_matched"
        fi ;;
    esac

    if [ -z "$mnt" ]; then
      mnt="$TMPDIR/$NAME"
      mkdir -p "$mnt"
      if mount -o ro "$part" "$mnt" 2>/dev/null; then mounted_here=1
      else mnt=""; fi
    fi

    if [ "$bootable" -eq 0 ] && [ -n "$mnt" ] && [ -d "$mnt" ]; then
      if [ -f "$mnt/EFI/BOOT/BOOTX64.EFI" ] || [ -f "$mnt/EFI/BOOT/BOOTIA32.EFI" ] || \
         [ -f "$mnt/EFI/BOOT/GRUBX64.EFI" ] || [ -f "$mnt/efi/boot/bootx64.efi" ] || \
         [ -f "$mnt/bootmgr" ] || [ -f "$mnt/bootmgr.efi" ] || \
         [ -f "$mnt/sources/boot.wim" ] || [ -f "$mnt/sources/install.wim" ] || \
         [ -f "$mnt/isolinux/isolinux.bin" ] || [ -f "$mnt/syslinux/syslinux.cfg" ] || \
         [ -f "$mnt/ldlinux.sys" ] || [ -f "$mnt/boot/grub/grub.cfg" ] || \
         [ -f "$mnt/boot/grub2/grub.cfg" ] || [ -f "$mnt/live/filesystem.squashfs" ] || \
         [ -d "$mnt/live" ] || [ -d "$mnt/casper" ] || [ -f "$mnt/.disk/info" ]; then
        bootable=1; reason="boot_heuristics_matched"
      fi
    fi

    [ "$mounted_here" -eq 1 ] && umount "$mnt" 2>/dev/null

    if [ "$bootable" -eq 1 ]; then
      device_detected=1
      reasons="$(add_csv_unique "$reasons" "$reason")"
      labels="$(add_csv_unique "$labels" "$LABEL")"
    fi
  done < <(lsblk -P -n -o NAME,FSTYPE,LABEL,MOUNTPOINT "/dev/$dev")

  if [ "$device_detected" -eq 1 ]; then
    echo "USB_BOOTABLE_MEDIA_DETECTED device=/dev/$dev reasons=${reasons:-unknown} labels=${labels:-none}"
    found=1
  fi
done

[ "$found" -eq 0 ] && echo "USB_BOOTABLE_MEDIA_NOT_DETECTED"
exit 0
```

Set correct permissions:

```bash
chmod 750 /var/ossec/active-response/bin/check_usb_bootable.sh
chown root:wazuh /var/ossec/active-response/bin/check_usb_bootable.sh
```

The script uses `lsblk` to find USB disks by transport type, then walks through their partitions one by one. For each partition it checks filesystem type and label first since those are fast and require no mounting. If those checks are inconclusive, it mounts the partition read-only into a temp directory and inspects the file structure. Everything gets cleaned up after inspection.

The output is intentionally simple, one of two strings:

```
USB_BOOTABLE_MEDIA_DETECTED device=/dev/sda reasons=common_boot_label_matched labels=KALI
USB_BOOTABLE_MEDIA_NOT_DETECTED
```

Keeping the output this clean makes the Wazuh rule matching easy to write and easy to read later.

## Agent configuration

Add this block inside `<ossec_config>` in `/var/ossec/etc/ossec.conf` on the agent:

```xml
<wodle name="command">
  <disabled>no</disabled>
  <tag>usb_bootable_check</tag>
  <command>/var/ossec/active-response/bin/check_usb_bootable.sh</command>
  <interval>5s</interval>
  <ignore_output>no</ignore_output>
  <run_on_start>yes</run_on_start>
  <timeout>10</timeout>
  <skip_verification>yes</skip_verification>
</wodle>
```

The `command` wodle runs the script on a scheduled interval and forwards the output to the manager for rule matching. Five seconds is fast enough to catch something without hammering the system. The 10 second timeout prevents a hung mount from blocking the agent.

Restart the agent after saving:

```bash
sudo /var/ossec/bin/wazuh-control restart
```

## Detection rules

On the Wazuh manager, add these to `/var/ossec/etc/rules/local_rules.xml`:

```xml
<group name="usb_boot_media,custom,linux,">

  <rule id="100251" level="8">
    <decoded_as>command</decoded_as>
    <match>USB_BOOTABLE_MEDIA_DETECTED</match>
    <description>Bootable USB media detected on Linux endpoint</description>
    <group>usb_boot_media,policy_violation,linux,</group>
  </rule>

  <rule id="100252" level="0">
    <decoded_as>command</decoded_as>
    <match>USB_BOOTABLE_MEDIA_NOT_DETECTED</match>
    <options>no_log</options>
  </rule>

</group>
```

Rule 100251 fires at level 8 when bootable media is found. Rule 100252 handles the expected negative output and suppresses it completely with `no_log`. Without that second rule, every clean poll generates a log entry and the noise adds up fast.

Restart the manager:

```bash
/var/ossec/bin/wazuh-control restart
```

## Validating the pipeline

Test the script directly on the agent first before depending on Wazuh automation:

```bash
sudo /var/ossec/active-response/bin/check_usb_bootable.sh
```

Then watch the manager alert log in real time:

```bash
tail -f /var/ossec/logs/alerts/alerts.json
```

Testing the script manually first is worth the extra step. If something is wrong with the detection logic you want to find out before you are wondering why alerts aren't coming through. Validating script, agent, rule, and alert separately makes troubleshooting a lot less painful.

## A note on active response

Wazuh supports an active response that unmounts USB partitions and removes the device from the kernel device tree via `/sys/block/$dev/device/delete`. It works, but in most environments automatic containment should be treated as an advanced option rather than the default.

The detection is heuristic. Some USB devices may be legitimately needed by the user. And Wazuh can only act after the device has already been visible to the OS, so containment is always reactive. Triggering an automatic response based on a label match and accidentally cutting off a legitimate device is a real possibility.

In practice this kind of use case works best as detection with SOC review first, with containment reserved for high-risk assets or repeated detections from the same host.

## What this catches and what it doesn't

This will reliably detect common Linux live media like Kali, Ubuntu, Tails, Fedora, and Arch, along with Windows installer media, Ventoy multi-boot drives, and most EFI-bootable recovery tools.

It won't catch custom or unlabeled boot media that avoids known filesystem patterns, devices that were connected and removed before the agent polled, or anything that happened before the monitored OS loaded.

That last point is worth internalizing. Host-based detection has a hard floor at OS boot time. For complete coverage, USB boot controls need to be enforced at the firmware level with BIOS/UEFI boot order restrictions and a firmware password. This Wazuh detection is a useful layer on top of that, but it's not a replacement for it.
