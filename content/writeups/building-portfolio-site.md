---
title: "Building my portfolio site with Hugo and GitHub Pages"
date: 2025-04-03
tag: "project"
draft: false
---

I wanted a portfolio site that actually looked like something I built rather than something I dragged and dropped together. Most security portfolio sites look identical, a template with a headshot, a skills progress bar, and a contact form. I wanted something cleaner and more intentional, so I built mine from scratch using Hugo and deployed it on GitHub Pages with a custom domain.

This writeup covers how I built it, the problems I ran into, and the security decisions I made along the way.


# Choosing the stack

I went with Hugo as the static site generator for a few reasons. Static sites have a much smaller attack surface than something like WordPress, no database to inject into, no admin login panel to brute force, no server side code to exploit. The files GitHub Pages serves are just HTML, CSS, and JavaScript. There is genuinely not much to attack.

Hugo generates all the HTML at build time rather than at request time, which means the server never executes code when someone visits the site. For a security professional having a WordPress site with seventeen plugins would be embarrassing. A static site is the honest choice.

I built a completely custom theme rather than using a pre-built one. Pre-built themes look generic no matter how much you tweak them and I wanted something that actually felt like mine. The design direction was dark background, soft purple accent, clean modern typography, nothing neon or hacker cliched.

## Getting Hugo running

The first real problem I ran into was getting Hugo installed on Windows. The standard installation methods kept failing.

Running `winget install Hugo.Hugo.Extended` would just load forever without completing. When I tried the Scoop method with `irm get.scoop.sh | iex` it appeared to do nothing. Neither package manager was working reliably.

The fix was simpler than expected. I downloaded the Hugo extended binary directly from the GitHub releases page, created a `C:\Hugo\bin` folder, moved `hugo.exe` into it, and added that folder to my system PATH through the Windows environment variables GUI rather than through PowerShell. The GUI approach bypassed whatever was causing the PowerShell commands to freeze. After reopening a fresh terminal Hugo was working.

A version check confirmed it:

```
hugo v0.159.2+extended windows/amd64
```

## Building the theme

I structured the Hugo project with a fully custom theme folder rather than pulling in someone else's layout. The key files are a base template that every page inherits from, partials for the nav and footer that get included automatically, and separate layout files for the homepage, writeups list, individual writeup posts, and inner pages like about and projects.

One problem that cost me time was CSS changes not showing up in the browser even after saving the file. Hard refreshing with Ctrl+Shift+R did nothing. Opening DevTools and checking the Sources tab showed the CSS file was not even being served, Hugo was not picking it up from the theme's static folder.

The fix was running the dev server with the `--disableFastRender` flag, which forces Hugo to fully rebuild every file on every change instead of using its cache. That immediately resolved it.

## Deploying to GitHub Pages

Deploying to GitHub Pages with a custom domain involves a few moving parts that have to be set up in the right order.

First I pushed the project to a repository named `EduardoSec.github.io` following the GitHub Pages naming convention. The first push attempt failed because I had the remote URL wrong, I had used `EduardoSec` as the username when my actual GitHub handle is `Eduardo-Sec` with a hyphen. Once I corrected the remote URL the push went through.

For the build and deploy process I set up a GitHub Actions workflow that runs automatically on every push to master. The workflow checks out the code, sets up Hugo with the extended version, builds the site with minification, uploads the output as a Pages artifact, and deploys it.

Pointing my `ebustamante.dev` domain at GitHub Pages required adding four A records in Namecheap's Advanced DNS settings pointing to GitHub's Pages IP addresses, plus a CNAME record for the www subdomain. I also added a CNAME file to the repository root containing my domain so GitHub Pages knows which site to serve when a request hits their servers. The `.dev` TLD requires HTTPS which GitHub Pages handles automatically through Let's Encrypt once DNS propagates.

## Securing the workflow

After getting the site running my coworker on the DevOps team pointed out that my GitHub Actions workflow was using version tags for third party actions rather than pinning them to specific commit hashes. This matters because tags are mutable, if someone compromises a repository that publishes an action they can move the tag to point at a malicious commit and your workflow will run that malicious code on the next push. Pinning to a full commit hash is the only way to guarantee you are running exactly the code you audited.

This is not theoretical. In March 2025 the `tj-actions/changed-files` action was compromised exactly this way, more than 350 tags were updated to point at a commit that dumped runner secrets, affecting over 23,000 repositories.

I updated the workflow to pin the first party GitHub actions to their full commit SHA hashes. Third party composite actions like `peaceiris/actions-hugo` cannot be pinned by hash due to how GitHub resolves composite actions, so those stay on version tags which is an acceptable tradeoff.

I also set up Dependabot to monitor the workflow file weekly and open pull requests when newer versions of pinned actions are available. The configuration is straightforward:

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    commit-message:
      prefix: "chore"
```

One problem that came up with Dependabot is that when it opens a pull request, GitHub Actions runs the workflow on that PR branch. The deploy job was failing because PR branches are not allowed to deploy to the github-pages environment, only the master branch is. The fix was adding a condition to the deploy job to skip when the event is a pull request:

```yaml
if: github.event_name != 'pull_request'
```

This lets the build job run on Dependabot PRs and report a green status check so the PR can be merged, but nothing actually deploys until the PR is merged into master and a real push triggers the full workflow.

## Branch protection and environment settings

I set up a branch protection rule on master with two requirements. Status checks for both build and deploy must pass before anything can merge, which means a broken Hugo build cannot accidentally go live. Force pushes are blocked to prevent accidentally rewriting git history.

I also switched to a pull request based workflow rather than pushing directly to master. It adds a small amount of overhead but it mirrors how real teams work and it means every change goes through the build and deploy checks before going live.

## What the site runs on

The final stack is Hugo generating a fully static site, GitHub Actions building and deploying on every push to master, GitHub Pages serving the output, and Cloudflare's DNS pointing `ebustamante.dev` at GitHub's servers. No server side code, no database, no CMS login panel.

When the Bosgame P3 Lite home lab is set up the plan is to migrate to self hosting on an Ubuntu VM with Nginx and a Cloudflare tunnel for public access. The tunnel means my home IP is never exposed, Cloudflare proxies all traffic through their network. The domain stays the same and only the destination changes.

## Takeaways

Building the site from scratch rather than using a template took more time upfront but the result is something that actually feels like mine. The security decisions along the way, pinning action hashes, setting up Dependabot, restricting the Pages environment, are small details but they are the kind of thing that shows you think about this stuff seriously rather than just going through the motions.

The site is live at ebustamante.dev. Source is on GitHub if you want to see how it is put together.
