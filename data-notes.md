# Data notes

Source: e-Sbírka open data (SPARQL), informativní znění, fetched 2026-10-28 with scripts/fetch.py.
Scope: see the scope table in the plan. Labels (keep/drop) live in the NájemAI corpus artifact; the load script includes only § marked keep.

## Labeling result (2026-10-28)
133 § labeled: 124 keep, 9 drop.

Dropped (cannot answer a tenant question):
- NV 308/2015 § 1: úvodní ustanovení.
- NV 308/2015 § 7, zákon 67/2013 § 15: účinnost.
- Zákon 67/2013 § 14: přechodná ustanovení from 2013.
- The other five drops are listed in the artifact table.

Kept after review (were unsure or unlabeled):
- OZ § 2235: defines when the nájem bytu rules apply; odst. 2 is the short-term rental exception.
- OZ § 2239: zakázaná ujednání; the only OZ § changed in 2026 (odst. 2), so it is the main date-sensitive test.
- OZ § 2218: default rule for when rent is due (měsíčně pozadu). Initially dropped, reversed.
- OZ § 2207: who does maintenance and repairs; core.
- OZ § 2294: fixtures attached to the flat.
- OZ § 2203 (nájem v katastru), § 2297 (služební byt): niche but valid.
- Zákon 67/2013 § 10: extends the rules to houses divided into units without an SVJ.
- OSŘ § 173: referred to by § 175a odst. 4.

Rule used: drop only what cannot answer a tenant question (úvodní ustanovení, účinnost, přechodná ustanovení). Keeping a rarely retrieved § costs one or two rows.

## Structure observations
- Text contains inline HTML links to other provisions (`<a class="int_odkaz">§ 4</a>`) and double spaces. The parser strips tags, keeps the link text and collapses whitespace.
- Headings (Nadpis_nad, Nadpis_pod) are stored as separate fragments, not as part of a §. They give context (e.g. "Jistota") but are not citable.
- A § with a single unnumbered paragraph stores its text in a fragment without a citation (e.g. § 2276, frag_7991305). The parser must take the § from the parent path and set odst to null.
- OSŘ § 175a, 195 and 196 do not exist before the 2026-01-01 version (added by zákon 176/2025 Sb.); fetch.py reports them as "not in this version" for older versions.

## Cross-references outside the corpus
- OZ § 2282a odst. 1 → § 899a odst. 1 OZ (majetek nezletilého). Rare case, left out; the assistant abstains on it.

## Unsure cases
- (none)

## Portal vs corpus differences
- (none found)
