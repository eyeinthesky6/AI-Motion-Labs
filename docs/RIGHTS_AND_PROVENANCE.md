# Rights and Provenance

Motion extraction is technically easy to confuse with permission to reuse motion. They are not the same thing.

This document is an engineering/product policy, **not legal advice**. Before a public motion marketplace or large-scale third-party ingestion launches, obtain jurisdiction-specific legal review.

---

# v0 rule: upload first

The first product path accepts **user-provided local files**.

The user is responsible for having the rights/permission needed to process and reuse the source for their intended purpose.

The platform records an attestation; it does not pretend to independently prove ownership.

Why this is the right starting point:

- it keeps the extraction problem separate from platform scraping/downloading terms;
- it works for owned studio footage, UGC, training videos and mobile recordings;
- it lets the core MotionSpec infrastructure mature before a public-content policy problem is introduced;
- it gives us a clean path to private enterprise libraries.

---

# YouTube is not the v0 ingestion pipe

As of the review date (2026-08-21), the YouTube API Services Developer Policies state that API clients must not download, import, back up, cache or store copies of YouTube audiovisual content without YouTube's prior written approval.

They also restrict using non-YouTube-API technology to access/retrieve YouTube API data/content.

Policy: https://developers.google.com/youtube/terms/developer-policies

Therefore the default product **must not** be:

```text
paste any YouTube URL → we download it → add derived motion to our library
```

A user may possess their own source file independently of YouTube and upload it. Future platform integrations must be reviewed separately and may require API authorization, written approval or another licensed acquisition route.

A source URL stored for provenance does not grant download or reuse rights.

---

# Source rights and derived-motion rights are separate questions

A MotionSpec asset may strip away the original pixels/background/identity, but that does not automatically make every resulting use rights-free.

Depending on the source and jurisdiction, relevant rights can include:

- copyright in the audiovisual work;
- choreography copyright in sufficiently original choreographic works;
- performer/contractual rights;
- publicity/personality rights;
- music rights when timing/sequence remains tied to music;
- confidentiality/trade-secret restrictions in enterprise footage;
- platform terms of service;
- dataset/model licenses.

This is why the manifest stores provenance and reuse policy instead of saying “derived = ours.”

---

# Current MotionSpec rights fields

```text
source_attestation
public_share_allowed
commercial_reuse_allowed
license_id
source_url
notes
```

## `source_attestation`

Allowed v0 values:

- `user_claims_rights`
- `licensed`
- `public_domain`
- `open_license`
- `unknown`

This is an **assertion category**, not proof.

## `public_share_allowed`

Default: **false**.

Extraction does not flip this flag. A future sharing workflow must make it an explicit rights/user decision.

## `commercial_reuse_allowed`

Tri-state in v0 (`true`, `false`, unknown). Unknown is intentionally different from false.

## `license_id`

Examples later might include SPDX-style identifiers for open material or an internal license/grant ID for enterprise content.

## `source_url`

Optional provenance pointer only. Never treat the presence of a public URL as evidence that content can be downloaded, derived, redistributed or sold.

---

# Public library policy — future

A public/shared library should be an **opt-in curated layer**, not a dump of everything users process.

Eligible categories should initially be limited to:

1. user-created motion where the uploader explicitly grants sharing/reuse rights;
2. commissioned/first-party studio motion with a written grant;
3. properly licensed motion datasets/assets whose terms permit the intended redistribution/commercial use;
4. public-domain material where status is actually established;
5. synthetic/first-party generated motion with compatible model/output rights.

Do not make `upload one, unlock two` automatically publish uploads. Credits can reward an explicit rights-cleared contribution, but the private vault remains the default.

---

# Private / team / public visibility

Future hosted product should have three separate visibility states.

## Private vault

- visible only to owner;
- best default for all uploads;
- rights may still restrict the owner's downstream use, but the system is not redistributing to strangers.

## Team library

- organization/workspace access;
- valuable for agency/brand/industrial workflows;
- enterprise confidentiality/access controls matter as much as copyright.

## Public library

- explicit opt-in;
- requires stronger attestation/license metadata;
- moderation/takedown process;
- provenance displayed to downstream users;
- commercial reuse filters.

---

# Do not bundle source video into MotionSpec by default

The portable `.motion` asset contains:

- technical source fingerprint;
- extracted/derived motion arrays;
- provenance metadata;
- optional previews/exports whose rights permit retention.

It does **not** need to contain the original video.

Benefits:

- smaller reusable asset;
- easier source-media deletion/retention policy;
- reduced accidental redistribution;
- exact hash can still link a derived asset back to its processing source internally.

The hosted service may retain private source media for a user-defined period to allow reprocessing, but that is a product/storage policy rather than a requirement of MotionSpec.

---

# Proposed ingestion lifecycle

```text
upload source
    ↓
collect rights attestation
    ↓
hash + private storage
    ↓
extract MotionSpec
    ↓
private by default
    ↓
optional explicit share flow
    ↓
rights checks / license metadata / moderation
    ↓
team or public library
```

The extraction worker should not contain business logic that decides sharing rights.

---

# Model and dataset provenance

The asset's source video is only one side of provenance. The **producer stack** can carry license obligations too.

For an extraction/enrichment run, track:

- code/package name and version;
- model/checkpoint name/hash;
- model/checkpoint license;
- body model dependency/license;
- whether training-data terms materially constrain checkpoint use;
- adapter version/options.

Examples that matter to this project:

- MediaPipe code is Apache-2.0, but downloaded model/task artifacts should still be reviewed;
- MMPose code is Apache-2.0, but individual checkpoints/data can carry separate terms;
- MotionBERT code is Apache-2.0, while its research datasets have separate terms;
- WHAM code is MIT but uses separately licensed body-model/dependency assets;
- GVHMR upstream software license is non-commercial unless separately licensed;
- SMPL/SMPL-X academic model terms are non-commercial, with separate commercial licensing;
- Motion-X access is explicitly framed for non-commercial use and inherits constituent dataset terms.

This is why “the repo says MIT” is not enough for an ML product.

---

# Deletion and takedown — future hosted service

At minimum support:

- user deletion of source media;
- user deletion of derived private assets;
- lineage lookup from source hash → derived assets;
- de-publication without deleting audit history immediately;
- takedown/rights-dispute status;
- disabling new exports/reuse during a dispute;
- documented retention period for backups/logs.

If a public library launches, add a clear copyright/takedown process before scale.

---

# Enterprise footage

Industrial/training video creates a different problem: the company may own/control the footage but still consider it confidential.

Future enterprise controls should include:

- private workspaces;
- regional/object-storage controls if needed;
- source-media retention limits;
- no-training/no-public-reuse contractual flags;
- access logs;
- explicit separation between a customer's private motion library and any global/public corpus.

A useful default principle:

> **Customer private motion never trains or enriches a public library unless the customer separately opts in.**

---

# First-party seed library

To avoid depending on legally ambiguous internet video, we can create a small commercially clean seed corpus ourselves.

Examples:

- walk/run/turn;
- reach/pick/place;
- point/present;
- unbox/show product;
- basic hand gestures;
- sit/stand/crouch;
- safe dance-like motion loops.

Record with consent/release and store the grant alongside the assets.

Twenty deliberately chosen first-party clips are more useful for engineering than twenty thousand questionable downloaded clips.

---

# Product copy rule

Do not promise:

> “Turn any video on the internet into a commercially reusable motion.”

Safer/correct positioning:

> “Turn video you are entitled to use into a reusable motion asset.”

The technology can be broad while the ingestion policy remains sane.

---

# Open questions before public sharing

1. What license/grant do contributors give the public library?
2. Can an uploader withdraw future reuse, and what happens to already-exported assets?
3. How do we handle recognizable/choreographed signature performances?
4. What provenance must a downstream buyer/user see?
5. Can public assets be used for commercial ads, model training, or only rendering?
6. Do we permit derivative edits/remixes?
7. What is the takedown/dispute process?
8. Do we fingerprint incoming motion against disputed/removed assets?

None of these questions blocks the private `video → MotionSpec` foundation.
