# Design decisions

- **Separation of authority:** trusted instructions live in code, never in retrieved JSON. Every excerpt has `trust=untrusted_evidence`.
- **Fail-closed filtering:** a tenant mismatch, missing role, or expired record excludes a source before selection.
- **Bounded optimization:** input excerpt count, excerpt byte length, and budget range are validated. A dynamic-programming knapsack optimizes a pre-scored evidence set without fractional excerpts.
- **Deterministic output:** stable sorted evidence IDs make replay and regression testing simple.
- **Privacy hygiene:** redaction runs before prompt serialization, and the HTML report is generated from redacted prompt output and excerpt IDs only.
- **Bounded claims:** token approximation and PII patterns are illustrative. A real implementation needs provider tokenization, verified identity, trusted ACL enforcement, proper DLP, and adversarial prompt testing.

The threat model assumes untrusted retrieved snippets may contain instructions, private fields, or references to other tenants. It does **not** assume an attacker can rewrite the trusted Python module or alter the authoritative role/tenant request context.

## Nice extension ideas

Replace preassigned scores with retrieval rerankers, integrate tokenizers for the chosen model, add signed data provenance, and measure abstention/citation faithfulness using a human-reviewed evaluation set.
