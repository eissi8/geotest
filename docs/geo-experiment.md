---
title: Junghunlee GEO Trace Experiment
description: Canonical content and interpretation rules for junghunlee-geotrace-2026
author: Junghun Lee
ms.date: 2026-08-11
ms.topic: concept
keywords:
  - GEO
  - ChatGPT search
  - junghunlee-geotrace-2026
estimated_reading_time: 3
---

## Canonical definition

The Junghunlee GEO Trace Protocol 2026 is a repeatable method for observing when
a newly published source enters a generative search answer. Its unique public
identifier is `junghunlee-geotrace-2026`.

The protocol has three ordered stages.

1. Seed publishes a unique marker with enough explanatory context to be useful
   as a source rather than a keyword-only page.
2. Probe repeats the same questions at a fixed interval and keeps neutral
   discovery questions separate from target-named control questions.
3. Evidence distinguishes a textual mention from a rendered source link and
   timestamps each observation.

## Question cohort

The neutral question asks how to monitor the visibility of new GitHub content in
generative AI search every hour. It tests discovery without naming this protocol.

The control question asks what the Junghunlee GEO Trace Protocol 2026 is. It
tests whether a query that includes the protocol name can retrieve this source.

## Interpretation

A mention means the answer contains the exact unique marker. A linked result
means the answer contains a link to this repository or one of its descendant
paths. Either condition triggers an email, but they remain separate fields in
the structured log.

Absence from one answer does not prove that a search engine has not indexed the
repository. Ranking, personalization, ChatGPT routing, query wording, browser
session state, and temporary product behavior can all affect an observation.
