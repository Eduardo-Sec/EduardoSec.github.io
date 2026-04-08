---
title: "Automating the portfolio site, link checking, spell checking, Lighthouse, and security audits"
date: 2026-04-08
tags: ["project"]
draft: false
---

## Overview
The site already had one GitHub Actions workflow handling build and deploy with pinned commit hashes and Dependabot monitoring the workflow file weekly. That covered getting the site live but nothing was checking the quality of what went live. This covers five new workflows I added to automate that side of things, broken link detection, spell checking, performance auditing, security header monitoring, and keeping security.txt compliant automatically.

The foundation was already there. Pinned commit hashes, branch protection, PR workflow. These five workflows build on top of that rather than replacing anything. The goal was catching different categories of problems automatically so I am not manually checking things that a workflow can handle.

---

## Link checker

The link checker uses `lycheeverse/lychee-action` pinned to a commit hash. It runs on push to master, on pull requests against master, and on a weekly Monday schedule via cron. The weekly schedule is the most valuable part since links rot over time without any code changes triggering a check. A link that was valid when I published a writeup can break six months later and I would never know without something checking it automatically.

The first run failed immediately with "Cannot convert path to URI" errors. Lychee was trying to scan the local repository files and could not resolve root-relative links like `/about` or `/css/main.css` because those paths only make sense in the context of the live site. The fix was adding the `--base` flag pointing to `ebustamante.dev`, which tells lychee to resolve all root-relative paths against the live domain rather than the runner filesystem.

I also excluded LinkedIn from the checks. LinkedIn blocks automated requests and always returns failures, so without excluding it the workflow would fail on every run regardless of whether the link is actually broken. The `GITHUB_TOKEN` gets passed through to avoid GitHub rate limiting on links pointing to GitHub repos.

---

## Spell checker

The spell checker uses `streetsidesoftware/cspell-action` pinned to a commit hash. The most important decision here was scoping it correctly. It only triggers when markdown files inside the `content` directory change, not on every push. Workflow file changes, CSS changes, and template changes do not fire it. This keeps it focused on actual content and avoids noise from infrastructure work.

It requires two supporting files. A `cspell.json` config at the repo root that points to a custom wordlist, and a `project-words.txt` file containing terms that are not in any standard dictionary. Without the wordlist the checker fails on almost every technical writeup since security tool names, framework acronyms, and proper nouns like NebraskaCYBER are not in any standard dictionary. The wordlist covers cybersecurity terms, tool names, Hugo-specific terminology, and anything else that would cause false failures on legitimate content.

---

## Lighthouse CI

Lighthouse runs using `treosh/lighthouse-ci-action` pinned to a commit hash. It only runs on pull requests against master, not on every push. The reasoning is that the goal is catching regressions before they merge, not auditing every commit after the fact.

It audits three URLs on the live site, the homepage, the writeups page, and the about page. Running against the live site rather than a local build gives more accurate results since it reflects what real visitors see, including CDN behavior and caching. Reports get uploaded to a public storage URL posted in the workflow logs, and the full report saves as a downloadable artifact on the workflow run.

First run scores on the homepage were Performance 92, Accessibility 94, Best Practices 96, SEO 100. A few things came out of the report worth noting. Google Fonts is blocking render for about 770ms which is the main performance drag. The accessibility deduction came from contrast failures in the SOC dashboard where `.soc-stat-label` and `.soc-feed-status` use dim colors on dark backgrounds that do not meet WCAG contrast ratios. Best Practices lost points for a missing `favicon.ico` causing a 404, and for missing security headers like CSP which are a GitHub Pages limitation rather than something I can fix without server control.

The contrast issue is fixable and worth addressing. The security headers are deferred to the Nginx migration.

---

## Security headers check

This one uses no third party actions at all, just `curl` and bash built into the Ubuntu runner. That means no commit hash to pin and no supply chain risk from an external dependency. It runs on push to master and on a weekly Monday schedule.

The workflow fetches response headers from the live site and checks for the presence of seven headers, `strict-transport-security`, `x-content-type-options`, `x-frame-options`, `referrer-policy`, `permissions-policy`, `content-security-policy`, and `cross-origin-opener-policy`.

Results from the first run showed `strict-transport-security` is present with `max-age=31556952`, which GitHub Pages sets automatically for custom domains using HTTPS. All other six headers are missing. The workflow does not fail the build on missing headers since GitHub Pages does not support setting custom response headers at the server level. They are all deferred to the Nginx migration where adding them will be a few lines of config. The workflow exists as a persistent audit and reminder of what is outstanding rather than a gate that would block deployments on a limitation outside my control.

---

## Auto-update security.txt expiry

RFC 9116 requires an `Expires` field in `security.txt`. The file did not have one, so I added it set to one year out. The problem with a hardcoded expiry date is that it eventually lapses if I forget to update it, which would make the file technically non-compliant.

The workflow handles this automatically. It runs on a weekly Monday schedule and also supports `workflow_dispatch` for manual triggering. It reads the `Expires` field directly from the repo file, calculates how many days remain, and if within 30 days of expiry it updates the date to one year from the current date, creates a branch, commits the change, and opens a pull request automatically using the GitHub CLI with the `GITHUB_TOKEN`. If more than 30 days remain it exits cleanly with a log message.

The `workflow_dispatch` trigger was useful for testing without waiting for the Monday schedule. Triggering it manually confirmed the date calculation and PR creation worked before relying on the cron schedule.

---

## What changed overall

The repo now has automated checks covering broken links, spelling errors in content, performance and accessibility regressions, security header posture, and security.txt compliance. Most run on PRs so problems surface before they go live. The link checker and header check also run weekly so they catch drift over time, things that break without any code change on my end.

The security headers workflow in particular is useful not as a quality gate but as documentation. Every time it runs it confirms what is in place and what is deferred. When the Nginx migration happens those six missing headers become a checklist rather than something I have to remember from scratch.

All five workflow hashes were independently verified from the GitHub releases pages rather than trusting values from documentation or third party sources. Same process as the original deploy workflow.