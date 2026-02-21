---
name: general
description: a general prompt for KIRA AI to follow when generating new page UI, ensuring a consistent monochrome design system and locked layout structure across all pages.
model: GPT-5.3-Codex (copilot)
tools: [execute, read, edit, search, web, agent, todo]

---
Use this template as the base context before generating any new page.

This defines:

Design laws

Layout architecture

Component discipline

Tech stack constraints

Anti-drift rules

It is not a page.
It is the system.

1️⃣ CORE DESIGN PHILOSOPHY

The interface must feel:

Institutional

Analytical

Secure

Controlled

Executive-grade

Compliance-oriented

It must NOT feel:

Startup flashy

Marketing-heavy

Color-driven

Playful

Decorative

2️⃣ STRICT MONOCHROME SYSTEM (NON-NEGOTIABLE)
Global Color Tokens (Do Not Deviate)

No pure black (#000000)
No pure white (#FFFFFF)
No colors
No gradients
No glow
No accent hues

Use only controlled grayscale spectrum:

--bg-primary: #0E0E10;
--bg-secondary: #141416;
--surface-primary: #1A1A1D;
--surface-card: #1F1F23;
--surface-elevated: #25252A;
--border-primary: #2E2E34;
--border-soft: #2A2A2F;
--text-primary: #E8E8EA;
--text-secondary: #B8B8BD;
--text-muted: #8A8A90;
--text-disabled: #5A5A60;

All UI must use these tokens.

Depth is created using:

Layer contrast

Border tone

Elevation

Opacity variation

Never color.

3️⃣ PRODUCTION TECH STACK (MANDATORY)

All UI must assume the following stack:

Framework

React (Vite or Next.js App Router)

Styling

Tailwind CSS (using design tokens mapped to CSS variables)

Components

shadcn/ui (base components)

Radix primitives (for accessibility and composability)

Animation

Framer Motion (subtle transitions only)

Charts

Recharts (strictly monochrome themed)

Recommended Production Additions

clsx / tailwind-merge (class control)

React Hook Form (forms)

Zod (validation)

Zustand or Redux Toolkit (state)

TanStack Query (server state)

React Table (data tables)

Heroicons (stroke icons only, no filled color icons)

4️⃣ GLOBAL LAYOUT ARCHITECTURE

Every page must follow this container hierarchy:

<AppShell>
   <Sidebar />
   <TopBar />
   <MainContent>
       <PageHeader />
       <SectionBlocks />
   </MainContent>
</AppShell>

All new pages render only inside:

<MainContent />

No page is allowed to:

Re-style sidebar

Re-style top bar

Introduce alternate layouts

Break container rhythm

5️⃣ SPACING SYSTEM (LOCKED)

Base unit: 8px scale

Section spacing: 48px

Card spacing: 32px

Internal padding: 24–32px

Border radius: 12px

Max width: 1280px

No inconsistent spacing.

6️⃣ COMPONENT RULES
Cards

Background: surface-card

Border: border-primary

Rounded: 12px

No heavy shadows

Hover = subtle surface shift only

Tables

Header slightly darker than body

No zebra striping unless extremely subtle

Hover row = surface elevation

Status representation through:

Font weight

Opacity

Border tone
Never through color.

Buttons

Primary:

Background: surface-elevated

Border: border-primary

Text: text-primary

Hover: slight brightness shift

Secondary:

Transparent

Border only

No bright filled buttons.

Inputs

Background: bg-secondary

Border: border-soft

Focus: border-primary slightly brighter

No blue focus rings

Charts (Recharts Theming)

Only grayscale stroke colors

No legend color markers

Lines differentiated by:

Stroke width

Dash pattern

Tooltips styled in surface-card

7️⃣ ANIMATION RULES (Framer Motion)

Allowed:

Fade in (opacity)

Subtle slide (4–8px)

Gentle scale (1.02 max)

Section stagger entrance

Not allowed:

Bounce

Elastic

Spring exaggeration

Dramatic movement

Animations must feel executive and controlled.

8️⃣ PAGE GENERATION PROTOCOL

Every page must follow:

1. PageHeader
2. KPI or Overview Row (if relevant)
3. Primary Functional Section
4. Secondary Insight Section
5. Supporting Panel

Never freestyle layout.
Never invent new structural rhythm.

9️⃣ STABILITY & ANTI-DRIFT RULE

If a future prompt conflicts with this template:

Preserve:

Monochrome palette

Layout hierarchy

Spacing scale

Component structure

Token system

Override only:

Internal content

Data

Section titles

Never override:

Base structure

Design tokens

System architecture

This ensures the system behaves like a reusable enterprise template.

🔟 PRODUCTION-GRADE REQUIREMENTS

All generated UI must:

Be responsive

Be accessible (ARIA compliant via Radix)

Support keyboard navigation

Maintain contrast ratios

Avoid hardcoded inline colors

Use reusable components

Follow separation of concerns

FINAL USAGE INSTRUCTION

Before generating any new page, prepend:

Use KIRA AI Monochrome Enterprise Production Template.

This activates:

The design system

The component discipline

The architectural rules

The anti-drift protection