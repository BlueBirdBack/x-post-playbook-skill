# Persona Patch Pattern (steipete 2020704611640705485)

Source: https://x.com/steipete/status/2020704611640705485

## Core pattern

A high-impact post uses a **copy-paste prompt** to change agent behavior fast.

It works because it is:

1. concrete (specific do/don’t rules)
2. testable (you can observe behavior change quickly)
3. opinionated (clear direction, not generic advice)

## Extraction template for similar posts

When a post suggests "prompt-level behavior tuning", extract:

1. **Target behavior**
   - what should change (tone, brevity, confidence, etc.)

2. **Mechanism**
   - how change is applied (rewrite SOUL.md, system rules, memory policy)

3. **Guardrails**
   - what must never be weakened (safety, privacy, approval boundaries)

4. **Evaluation checks**
   - what success looks like after patching

## Recommended response style

- Acknowledge why the patch is powerful.
- Keep the useful parts.
- Add explicit safety/context boundaries.

## Why this matters

Turns "be better" into operational behavior design while avoiding personality drift into unsafe modes.
