import type { PropsWithChildren } from "react";

type SectionCardProps = PropsWithChildren<{
  title: string;
  subtitle?: string;
}>;

export function SectionCard({ title, subtitle, children }: SectionCardProps) {
  return (
    <section className="kira-card kira-card-hover" aria-label={title}>
      <header className="mb-6">
        <h2 className="text-base font-semibold text-text-primary">{title}</h2>
        {subtitle ? <p className="mt-2 text-sm text-text-muted">{subtitle}</p> : null}
      </header>
      {children}
    </section>
  );
}
