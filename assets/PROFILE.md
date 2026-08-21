# MEASURED PROFILE

*Generated 2026-08-21T13:13:35.920345Z for [@4444J99](https://github.com/4444J99). Counts come from the GitHub API; derived observations name their transformation. No percentile ranking is published because this repository does not carry a validated population distribution.*

## GitHub contribution activity (12 months) — **measured**

**Observed:** 33,587 contribution events

GitHub reports 33,587 contribution-calendar events in the last 12 months. Associated API fields report 15,671 commits, 4,191 pull requests, 219 reviews, and 2,504 issues; these fields are not an additive breakdown.

**Definition:** GitHub GraphQL contributionsCollection and contributionCalendar.

**Boundary:** This is an activity count, not a count of shipped units. GitHub events vary in scope and do not establish review, merge, quality, or impact.

## Visible organization memberships — **measured**

**Observed:** 10 organizations

GitHub returned 10 organization memberships for this account.

**Definition:** GitHub GraphQL user.organizations (first 20 visible to the token).

**Boundary:** Membership does not by itself establish ownership, administrative authority, or individual responsibility for every repository in an organization.

## Pull requests opened (12 months) — **measured**

**Observed:** 4,191 pull requests

GitHub reports 4,191 pull requests opened in the trailing 12-month collection.

**Definition:** GitHub GraphQL contributionsCollection.totalPullRequestContributions.

**Boundary:** Opened pull requests are activity events; this field does not say whether they were reviewed, mergeable, merged, distinct in scope, or created without automation.

## Visible non-fork repository corpus — **measured**

**Observed:** 290 repositories

290 non-fork repositories were visible across the personal account and 10 organization memberships returned by the API.

**Definition:** GitHub GraphQL repositories connections with isFork=false.

**Boundary:** Organization repositories can include work by other contributors. Visibility does not establish individual authorship, maintenance, or operation.

## Primary-language breadth of the visible corpus — **derived**

**Observed:** 17 primary-language labels

GitHub assigns 17 distinct primary-language labels across the visible non-fork corpus — led by Python (109), TypeScript (50), HTML (24), JavaScript (21), Shell (15).

**Definition:** Distinct repository.primaryLanguage.name values in the visible corpus.

**Boundary:** A repository has one GitHub-assigned primary language. This describes the corpus and does not establish individual proficiency or authorship.

## Mapped language-layer coverage — **derived**

**Observed:** 5 mapped layers

The static language map places the visible corpus in 5 layers: backend, creative, frontend, infra, native.

**Definition:** Deterministic primary-language-to-layer mapping in src/laurea/detectors.py.

**Boundary:** This is a corpus classification, not evidence that one person authored, shipped, or is proficient in every mapped layer.

## Account age — **derived**

**Observed:** 9.6 years

The GitHub account was created in 2016 (9.6 years ago).

**Definition:** GitHub GraphQL user.createdAt.

**Boundary:** Account age is not equivalent to continuous professional experience or activity.

## What these numbers do not establish

LAVREA reports an API-visible activity and repository corpus. It does not establish:

- individual authorship or responsibility for organization repositories
- code quality, correctness, maintainability, or security
- whether pull requests were reviewed, mergeable, or merged
- system reliability in production
- product adoption, user satisfaction, or business impact
- professional experience or engineering judgment

GitHub activity does not establish authorship, quality, reliability, adoption, or impact.
