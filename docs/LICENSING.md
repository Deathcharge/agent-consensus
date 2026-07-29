# Licensing decision record

Last reviewed: 2026-07-28

This document records the engineering recommendation; it is not legal advice. The repository's
current license is **MIT**, and no documentation in this file changes that grant.

## Recommendation

For a small, embeddable developer library whose goals are broad adoption, durable attribution, an
express patent grant, and separation of code rights from brand rights, the recommended future
license is **Apache License 2.0**, used without custom terms and accompanied by `NOTICE` and
`TRADEMARKS.md`.

Apache-2.0 is a better fit than MIT when “protected” means:

- contributors and users have an explicit patent license;
- distributors preserve applicable copyright, patent, trademark, and attribution notices;
- modified files are identified; and
- the software license does not grant rights to the Samsarix brand.

It remains permissive: downstream users may include the library in proprietary products and are not
required to publish their changes.

If “protected” instead means that distributed modifications to this library's covered files must
remain available as source, choose **MPL-2.0**. Its file-level copyleft is more protective of shared
improvements than Apache-2.0 while still allowing the library to be combined with larger proprietary
works. It adds compliance work and may reduce adoption among teams that accept only permissive
dependencies.

## Options

| License | Attribution and patent posture | Downstream obligation | Fit here |
| --- | --- | --- | --- |
| MIT (current) | Copyright and permission notice must be retained; no express patent clause | Minimal | Maximum simplicity, weakest protection mechanics |
| Apache-2.0 (recommended) | Express patent grant, notice preservation, changed-file notices, trademark exclusion | Permissive | Best adoption/protection balance |
| MPL-2.0 | Express patent grant and file-level copyleft | Distributed changes to covered files stay MPL/source-available | Best if improvement reciprocity matters more than friction |
| GPL/AGPL | Strong copyleft across a broader combined work; AGPL also addresses network use | Broad source-sharing duties | Usually too restrictive for an embedded library unless paired with a deliberate commercial dual-license model |
| Custom/BSL terms | Depends on bespoke drafting | Requires project-specific legal review | Not recommended without counsel and a concrete commercial model |

Primary references:

- [MIT License, Open Source Initiative](https://opensource.org/license/mit)
- [Apache License 2.0, Apache Software Foundation](https://www.apache.org/licenses/LICENSE-2.0)
- [MPL 2.0 license](https://www.mozilla.org/en-US/MPL/2.0/) and
  [Mozilla's MPL FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/)
- [GNU GPL FAQ](https://www.gnu.org/licenses/gpl-faq.en.html)

## Why the license was not changed automatically

The public repository already grants MIT rights to the versions published under MIT. A later
license choice cannot revoke copies already received under those terms. Relicensing also depends on
who owns the copyright in every contribution and whether any contributor consent is required.

Before the first public package release, the owner should explicitly choose one of:

1. retain MIT for `0.2.0`;
2. adopt unmodified Apache-2.0 for future releases; or
3. adopt unmodified MPL-2.0 for future releases.

For a change, confirm the copyright chain, replace `LICENSE` with the official unmodified text,
update the SPDX expression in `pyproject.toml` and `CITATION.cff`, update README/release notes, and tag
a clear version boundary. For MPL-2.0, also attach the license notice or SPDX identifier to covered
source files as Mozilla recommends. A qualified attorney should review the final choice if commercial
enforcement, dual licensing, patents, or contributor agreements matter.

`NOTICE`, `TRADEMARKS.md`, and `CITATION.cff` improve origin and citation clarity under the current
MIT license, but they do not add restrictions that MIT itself does not impose.
