---
title: "Redesigning the portfolio site, layouts, animations, and a SOC dashboard"
date: 2026-04-07
tags: ["project"]
draft: false
---

## Overview
The first two writeups covered building the site and adding features. This one covers tearing most of the visual layer apart and rebuilding it. The functionality was solid but the design felt generic. The terminal widget on the homepage was the most obvious problem since I had seen it on enough other portfolios that it stopped feeling like mine. Everything else had the same issue in smaller ways, pages with narrow content columns leaving half the screen empty, section headers that blended into the background, inner pages that all looked the same regardless of what they were for.

This covers what I changed, why, and the problems I ran into along the way.

---

## The SOC dashboard

The terminal got replaced with a status dashboard panel styled after a SOC monitoring interface. The reasoning was that a terminal is a developer aesthetic, not a security analyst aesthetic. A status panel showing real operational data is more specific to what I actually do.

The panel shows four stats in a grid, writeup count pulled dynamically from Hugo using `{{ len (where .Site.RegularPages "Section" "writeups") }}`, days as analyst calculated in JavaScript from October 1 2025, certs in progress, and tools in stack. Below the stats is a feed of status items with color coded badges, green for active, purple for informational, yellow for work in progress. There is a live clock in the header that updates every second and a pulsing green dot indicating the SOC is online.

The count-up animation on the stat numbers was a small touch that makes the panel feel alive on load rather than just static text.

---

## Logo and section markers

The nav logo got a proper SVG treatment. The old `eb.dev` text in monospace was fine but it was just text. The new logo is a radar slash signal mark, concentric circles with a sweep line rendered as a 24 by 24 SVG using the purple accent color. It reads as cybersecurity without being a lock or a shield which felt too literal.

Section markers across the whole site changed from `//` to `▸`. The double slash was borrowed from code comments and I had seen it on enough other sites that it stopped feeling distinctive. The filled triangle is still monospace and technical but more visually distinct at small sizes.

---

## Page layout overhauls

The about page had the most obvious empty space problem. The content was a narrow prose column with nothing on the right side of the screen at desktop widths. I converted it to a two column layout with a sticky sidebar on the left showing structured fields for current role, degree, minor, concentrations, location, and links. The data lives in front matter so updating it does not require touching the template. The prose content sits in the right column and scrolls past the sticky sidebar.

The projects page was plain prose, which made sense when there were only a couple of projects but did not scale. I converted it to a card layout with front matter data driving each card. Cards have a status badge in one of three styles, warn for in progress waiting on something, info for actively in progress, and done for completed. Each card also has tag chips and an optional source link field.

The contact page replaced plain text links with styled cards, one per contact method. The email card gets a subtle purple accent treatment to signal it as the primary method without being heavy handed about it.

The PGP page got a two column layout matching the about page structure. A sticky sidebar on the left shows structured fields for key ID, fingerprint, algorithm, expiry, and the keyserver command. The key block renders in the right column. Previously it was all stacked vertically which made the long key block feel like it came out of nowhere.

The resume page got a dedicated layout file that pulls the download PDF button into the page hero section alongside a last updated timestamp that Hugo calculates automatically from the file modification date.

---

## Writeup page improvements

Individual writeup pages got a few additions. A table of contents collapsed by default that expands on click, matching the dark header bar style used in the tools grid. Code blocks now show the language name in the top right corner using `attr(data-lang)` on the code element, which Hugo populates automatically from the fenced code block language identifier. Headings got `scroll-margin-top: 80px` so anchor links account for the sticky nav height.

The code block backgrounds were a problem. Hugo's Dracula syntax theme injects inline `background-color` styles directly on the `pre` element which overrides CSS class rules. The fix was `!important` on the highlight pre selector, which I would normally avoid but the inline styles leave no other option.

Scroll fade-in animations got added to all inner page sections using IntersectionObserver. Elements start at `opacity: 0` and `transform: translateY(20px)`, then transition to visible when they enter the viewport. Once visible the observer stops watching the element. The effect is subtle enough that it does not feel gimmicky but adds some life to pages that were previously completely static.

---

## Technical problems worth documenting

The public folder being tracked in git caused merge conflicts on almost every PR. The public directory is Hugo's build output and gets completely regenerated on every build, so tracking it in git means every branch has different versions of the same generated files. The fix was adding `public/` to `.gitignore` and removing it from the git index with `git rm -r --cached public`. Any branch created after that point was clean.

Hugo's layout lookup caused problems when relying on type-based inference. The docs suggest that content in a given section will automatically use matching layouts, but in practice the lookup order was not behaving as expected for some page types. The reliable fix was adding explicit `layout:` fields in front matter pointing to named files in `layouts/_default/`. Explicit beats implicit for anything you actually care about rendering correctly.

PowerShell's `>` redirect operator outputs UTF-16 encoding by default. When I used it to export the GPG public key the resulting file had a UTF-16 BOM at the start which GitHub rejected when trying to add it as a GPG key. The fix was using `gpg --output publickey.asc --armor --export` instead of redirecting stdout. The `--output` flag writes the file correctly in ASCII armor format.

The GPG agent on Windows lost its connection to keyboxd a few times, causing commit signing to fail with "no secret key" even though the key was present in the keyring. The fix was removing `use-keyboxd` from `~/.gnupg/common.conf`. The keyboxd daemon is newer and not fully stable on all Windows setups.

---

## Backing up the key

Setting up a GPG key and using it for commit signing is only useful if you do not lose it. I backed up the private key to a VeraCrypt encrypted USB drive. The whole drive is encrypted rather than using a container file, which means anyone who plugs it in without the password sees nothing at all.

After copying the key to the drive I ran `cipher /w:C:\Users\username` to overwrite free space on the system drive. The standard `rm` command and even the recycle bin leave file data recoverable with forensic tools. The cipher command writes over the space the deleted file occupied, making recovery significantly harder. It is not a perfect solution for a spinning disk but it is better than nothing and works well on an SSD where the data has not been written over multiple times.

The private key file is now only in two places, on the encrypted USB and in the GPG keyring on my desktop. The USB is stored separately from the machine.

---

## What changed overall

The site went from functional to intentional. The layouts are specific to what each page actually needs to communicate rather than everything using the same narrow single column template. The SOC dashboard is something I have not seen on other portfolios which was the point. The technical problems along the way, the git conflicts, the GPG issues, the Hugo layout lookup, were all worth documenting because they are the kind of things that cost an afternoon if you do not know what to search for.

The source is on GitHub if you want to see how any of it is put together.