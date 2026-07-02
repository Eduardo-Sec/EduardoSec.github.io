---
title: "Redesigning the portfolio to emerald and gold, then hardening the whole stack"
date: 2026-07-01
tags: ["project"]
draft: false
---

## Overview

This session had two halves. The first was a full visual redesign of the site, dropping the purple accent for an emerald and gold palette on the same dark background, plus a handful of new features. The second was a full security hardening pass across Django, nginx, and the Rocky Linux server itself, done as a walkthrough so I actually understood each change instead of just pasting commands. In between I found and fixed a few things that had quietly fallen through the cracks during the original Hugo to Django migration. Software versions and specific values reflect the state at time of writing.

-----

## Color system and visual redesign

The old palette was purple, `#a855f7` primary with `#7c3aed` as the dim variant, on a neutral near-black background. The new one keeps the dark background but shifts it to a very slightly emerald-tinted black, `#0a0d0b` instead of `#0f0f0f`, with `#10b981` as the primary accent and `#c9a227` as a gold secondary reserved for highlight treatment. Text went from `#f4f4f4` to a true `#ffffff` for primary text.

The interesting part was tokenizing colors that had never been tokenized. The original CSS had a pile of one-off hardcoded values, `#22c55e` for active status dots, `#fbbf24` for warnings, half a dozen near-identical navy-tinted surface colors, cursor colors hardcoded separately in the JS from the CSS variable of the same intended color. All of that got pulled into proper tokens during the rewrite, `--ac-bright`, `--ac-dim`, `--gold-bright`, `--warn`, `--info`, each with matching `-bg` and `-border` variants. Doing this also surfaced a design opportunity, the old amber warning color and the new gold accent were close enough in hue that badges using both looked nearly identical. Splitting them into a genuinely distinct blue `--info` token fixed a real legibility problem on the SOC dashboard's status feed, not just a cosmetic one.

One mistake worth documenting since I only caught it after a user report, I initially made the trailing period in headings like "Eduardo Bustamante." a gradient from emerald to gold using `background-clip: text`. At heading size across multiple characters this reads fine, but on a single period character there isn't enough area for the gradient to resolve into two distinguishable colors, it just reads as a muddy olive. Fixed by dropping the gradient and using solid `var(--ac)` for anything smaller than the hero heading itself.

The hero section also picked up a subtle animated grid texture, a repeating-linear-gradient at low opacity layered under a radial glow, masked to fade out toward the bottom of the section. Pure CSS, no new JS.

-----

## New features

With the palette settled I added several small features on top of the existing HTMX and vanilla JS stack, no new frontend dependency for any of it.

A command palette triggered by Ctrl+K or clicking a search trigger button in the nav. It hits a small JSON endpoint that returns static pages plus title-matched writeups, rendered as a simple overlay with arrow key navigation and enter to jump. Reused the existing debounce pattern from the HTMX search box.

A reading progress bar on writeup pages, fixed to the very top of the viewport above the nav, filling based on scroll position within the post content. Paired with scroll-spy on the table of contents, using an IntersectionObserver keyed to the same heading anchor IDs the markdown renderer already generates, so no changes were needed to `core/markdown.py` at all.

Small sparkline SVGs on two of the SOC dashboard stat cards, hand-authored paths rather than pulling in a charting library, since the goal was a decorative "this feels alive" touch rather than real data visualization.

A featured writeup concept, a boolean field on the Writeup model with a small migration, surfaced as a gold star badge next to the title anywhere a writeup row appears.

A copy-as-markdown button on writeup pages. The naive approach of dropping the raw markdown into a `<script type="text/plain">` tag and reading `.textContent` looked like it would work but doesn't, Django's autoescaping corrupts anything with angle brackets or ampersands in code blocks since the HTML parser doesn't decode entities inside script tags. Django's `json_script` template filter is built for exactly this, it safely serializes the string and the JS side does a plain `JSON.parse` on the result.

A custom 404 page, JSON-LD structured data for SEO, and a print stylesheet for the resume page that hides the nav, cursor, and dashboard chrome when printed.

-----

## The RSS feed saga

While reviewing the redesign I mentioned the RSS feed and its nav link, which turned out to not exist at all. It was in the Hugo site, `/index.xml` with a nav link and autodiscovery tag, and it simply never got ported during the original migration. Added it back with Django's syndication framework, a small `Feed` subclass in `core/feeds.py`.

The Hugo site also had a nice trick, an `xml-stylesheet` processing instruction pointing at a `feed.xsl` file that made the raw feed render as a styled page when opened directly in a browser instead of showing raw XML. I wired the same thing into the Django feed by subclassing `Rss201rev2Feed` and injecting the PI after the XML declaration. It didn't work. Turns out Chrome has deprecated and is in the process of fully removing client-side XSLT support, so the trick that worked fine when the Hugo site was built no longer works in current Chrome regardless of what the server sends. Rather than depend on a browser feature that's actively being removed, I built a proper `/rss/` page as a normal Django template reusing the site's existing writeup-row components, with the actual feed URL displayed as a subscribe target. The raw `/index.xml` feed still exists for actual feed readers, the nav link now points at the styled landing page instead.

-----

## Django security hardening

Went through Django's built-in `manage.py check --deploy` command before and after each change, which is a genuinely good way to verify you're actually closing the gaps it flags rather than guessing.

HSTS, SSL redirect, and referrer policy were straightforward. The one real gotcha was CSRF. Cloudflare terminates TLS at the edge and the tunnel talks to nginx over plain HTTP internally, and Django 4's CSRF middleware checks the browser's Origin and Referer headers against a computed value that depends on `request.is_secure()` resolving correctly through that whole chain. It didn't, and the first time I tried logging into the admin panel behind the newly added Cloudflare Access layer I got a flat CSRF failure. The fix is `CSRF_TRUSTED_ORIGINS` set explicitly to the site's HTTPS origin, which sidesteps the proxy header computation entirely. This is apparently a common enough deployment gotcha that it's worth remembering for any future Django-behind-a-proxy work.

Rate limiting the two search endpoints, `writeup_search` and the command palette's `cmdk_search`, both run unindexed `icontains` queries. Rather than pull in `django-ratelimit` as a new dependency, given the dependency trouble described below, I wrote a small decorator using Django's built-in cache framework, a per-IP fixed window counter with a 429 response past the limit. The one honest caveat is that gunicorn runs two worker processes and the default in-memory cache isn't shared between them, so the real ceiling is closer to double the configured limit. Fine for a low traffic personal site, worth revisiting if that ever changes.

Also added `/admin/` behind a Cloudflare Access policy gating by email, so there are now two independent authentication layers, Cloudflare's edge challenge and Django's own login, rather than relying on Django credentials alone.

-----

## The redirect loop

Turning on `SECURE_SSL_REDIRECT` immediately broke the live site with an infinite redirect loop. The cause was nginx's `X-Forwarded-Proto $scheme` header. Since nginx itself only ever receives plain HTTP locally from the Cloudflare tunnel, `$scheme` always evaluates to http regardless of what protocol the original client used against Cloudflare's edge. Django saw that header, decided the request was insecure, and redirected to HTTPS, which came back through the exact same path and got redirected again, forever. The fix is to hardcode `X-Forwarded-Proto https` in the nginx config instead of trusting `$scheme`, which is safe here specifically because nginx is bound to loopback and the only thing that can reach it is the tunnel, which never relays anything that didn't arrive at Cloudflare's edge as HTTPS in the first place. Applied directly on the server first since the site was actively down, then synced back into the repo.

-----

## Nginx and server hardening

Nginx picked up `server_tokens off` to stop leaking the exact version string, a request body size cap since the site has no upload functionality, and a `limit_req` zone as a second independent rate limiter covering every path including the admin login, not just the two endpoints Django throttles itself.

Server hardening on Rocky Linux went SSH first. Confirmed via `sshd -T` rather than grepping the config file directly, since Rocky's sshd_config pulls in extra files via Include and grepping the main file alone can miss the actual effective setting. Generated a fresh ed25519 key, appended it to authorized_keys, and critically tested that key-based login worked from a brand new terminal window before touching password auth, keeping the original session open the whole time as a safety net. Only after confirming the new key worked did `PasswordAuthentication` and `PermitRootLogin` get set to no.

fail2ban went on watching sshd via the systemd journal, five failed attempts in ten minutes gets an hour long ban. A firewalld audit turned up something unexpected, a `cockpit` service exception open in the default zone that turned out to have nothing behind it, the actual cockpit package was never installed, just an unused firewall rule left over from the base image. Closed the rule anyway. Last piece was `dnf-automatic` with `apply_updates` flipped to yes and the timer enabled, so OS security patches land daily without needing to remember to run them manually.

-----

## Dependency management, the hard way

Somewhere in the middle of all this I noticed `.github/dependabot.yml` only covered the `github-actions` ecosystem, `requirements.txt` had zero Dependabot coverage despite the whole site being a Django app now. Added a `pip` block. Then, twice, a Dependabot PR bumping Django all the way to 6.0 and gunicorn to 26 got merged and broke the server, both packages require a newer Python than the Rocky 9 server actually has. Added an `ignore` rule for major version semver bumps after the first incident, and it happened again anyway, because the offending PR had already been opened before the ignore rule existed and the rule only prevents new PRs from being created, it doesn't retroactively close ones already sitting open. Reverted `requirements.txt` to the known-good pins both times and learned to actually check the open PR list after adding an ignore rule, not just trust it going forward.

-----

## What is deferred

Content-Security-Policy never actually got implemented. It's the one piece of the original hardening plan that got flagged as needing a real decision, several templates have inline script blocks for things like the SOC clock and the TOC toggle, and a strict CSP needs either `unsafe-inline` or a nonce-based rewrite of every one of those blocks. Worth doing properly rather than rushing.

HSTS is intentionally sitting at a conservative one hour with `includeSubDomains` and `preload` both off. Raising the duration and adding preload is a one-way door once submitted to browser preload lists, so that's waiting until HSTS has run clean in production for a while first.

Permissions-Policy headers were planned for the nginx layer and never actually added. The recolored `feed.xsl` stylesheet still exists for browsers that haven't deprecated client-side XSLT, Firefox and Safari reportedly still support it, but that wasn't actually verified against a real Firefox or Safari session, only Chrome, where it doesn't render regardless.
