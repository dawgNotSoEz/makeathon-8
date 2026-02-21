# KIRA v2

Use KIRA AI Monochrome Enterprise Production Template.

## Overview

KIRA v2 is an enterprise regulatory intelligence UI system with strict design governance and reusable page architecture.

## Implemented Pages

- `Dashboard` (`/dashboard`)
- `Document Registry` (`/documents`)
- `Document Intelligence Workspace` (`/documents/analysis/:documentId`)
- `Profile Settings / IAM` (`/profile`)

## Stack

- React + Vite + TypeScript
- Tailwind CSS (token-based monochrome theme)
- Radix UI primitives (`Tabs`, `Collapsible`, `Dialog`, `Switch`)
- Recharts (monochrome charting)
- Zustand, React Hook Form, TanStack Table
- Framer Motion

## Run

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```
