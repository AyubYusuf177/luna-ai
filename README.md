# Luna AI

Message-first agentic travel operator.

## Structure

```
apps/mobile       Expo + React Native + Tamagui
apps/web          Next.js (onboarding, settings, integrations, trips)
apps/storybook    Storybook — component stories and visual states

services/brain-api  FastAPI — agent runtime, planning, policy, channels
services/workers    Background workers — proactive engine, scheduled jobs

packages/ui         Shared Tamagui components
packages/tokens     Design tokens — colors, typography, spacing, radii
packages/contracts  OpenAPI-generated Zod schemas and TypeScript types
packages/config     Shared ESLint, TypeScript, and tooling configs

archive/legacy-v0.3.3  Reference implementation. Do not import from here.
```

## Requirements

- Node >= 20
- pnpm >= 9
- Python 3.12 (for services)

## Getting started

```bash
pnpm install
pnpm dev
```

## Design principles

- Messaging is the primary interface. SMS and WhatsApp are inbound channels, not bolt-ons.
- The app and web UI exist only for onboarding, integrations, vault, and settings.
- No capability is wired unless there is a real API behind it.
- No booking is claimed unless a confirmed booking event has been returned.
