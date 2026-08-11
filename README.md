---
title: ChatGPT GEO Trace Monitor
description: Hourly Playwright experiment for measuring whether ChatGPT discovers a target GitHub repository
ms.date: 2026-08-11
---

## Junghunlee GEO Trace Protocol 2026

`junghunlee-geotrace-2026` identifies an original experiment for measuring when
new public content becomes discoverable through ChatGPT web search. The protocol
uses three stages: Seed, Probe, and Evidence.

* Seed publishes a unique marker and a substantive explanation in a public
  repository.
* Probe asks fixed neutral and navigational questions through ChatGPT every hour.
* Evidence records answer mentions and rendered links separately, then sends an
  alert when either signal matches.

The marker, protocol name, and three-stage definition are the canonical facts
used by this repository's GEO test. See [experiment details](docs/geo-experiment.md)
for the question cohort and interpretation rules.

> [!WARNING]
> ChatGPT's website has no stable browser automation contract. Selectors, login
> sessions, bot defenses, and product terms can change. Review OpenAI's current
> terms before operating the scheduled browser.

## Local setup

Python 3.12 is required.

```powershell
python -m pip install -e ".[dev]"
python -m playwright install chromium
python -m pytest -q
```

Capture a ChatGPT session in a headed browser. Credentials are entered directly
into ChatGPT and are never handled by the application.

```powershell
geo-capture-session
```

The command creates `storage-state.json`. This authentication artifact is
ignored by Git and must be protected like a password. The capture removes a
large, nonessential Statsig evaluation cache before saving the session. The
command refuses to save unless the ChatGPT prompt is visible after login.

Verify the current ChatGPT DOM integration without sending email.

```powershell
python .\scripts\smoke_chatgpt.py
```

## Azure deployment

The deployment creates Azure Container Registry, Key Vault, Communication
Services Email, Log Analytics, a Container Apps environment, and an hourly
scheduled Job. Azure Container Registry builds the image remotely, so local
Docker is not required.

```powershell
.\infra\deploy.ps1 -Prefix geotrace
```

The schedule is `0 * * * *` in UTC. The first deployment uses an Azure-managed
email domain and sends matching answers to `junghunlee@microsoft.com`. Chromium
runs in headed mode through Xvfb because ChatGPT blocks the tested headless
browser locally. Cloudflare may still block Azure data-center traffic.

## Configuration

The primary settings are JSON arrays so multiple questions, terms, and target
URLs can be tested without rebuilding the image. Defaults are defined in
[configuration](src/geo_monitor/config.py).

## Security

The scheduled Job uses a fresh anonymous ChatGPT browser context by default. A
user-assigned managed identity pulls images and authenticates to Azure
Communication Services. No OpenAI API key or ChatGPT credential is used.
