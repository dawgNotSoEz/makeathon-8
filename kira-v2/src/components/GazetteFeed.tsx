import { useEffect, useMemo, useState } from "react";
import { apiClient } from "../api/client";

type GazetteRow = {
  id: string;
  subject: string;
  url: string;
  textPreview: string;
};

function normalizeGazettes(input: unknown): GazetteRow[] {
  if (!Array.isArray(input)) {
    return [];
  }

  return input
    .map((item, index) => {
      const record = typeof item === "object" && item !== null ? (item as Record<string, unknown>) : null;
      const id = String(record?.id ?? `gazette-${index}`);
      const subject = String(record?.subject ?? "");
      const url = String(record?.url ?? "");
      const text = String(record?.text ?? "");

      return {
        id,
        subject,
        url,
        textPreview: text.slice(0, 220),
      };
    })
    .filter((item) => item.subject.length > 0 || item.url.length > 0);
}

export function GazetteFeed() {
  const [gazettes, setGazettes] = useState<unknown>([]);

  useEffect(() => {
    let active = true;

    const loadGazettes = async () => {
      try {
        const response = await apiClient.getGazettes();
        if (active) {
          setGazettes(response);
        }
      } catch {
        if (active) {
          setGazettes([]);
        }
      }
    };

    void loadGazettes();
    return () => {
      active = false;
    };
  }, []);

  const rows = useMemo(() => normalizeGazettes(gazettes), [gazettes]);

  return (
    <section aria-label="Gazette feed">
      <h3 className="text-base font-semibold text-text-primary">Gazette Feed</h3>
      <p className="mt-1 text-xs text-text-secondary">Read-only records from gazette dataset.</p>

      <div className="mt-4 space-y-3">
        {rows?.slice(0, 8).map((item) => (
          <article key={item.id} className="rounded-md border border-border-soft bg-surface-primary p-4">
            <h4 className="text-sm font-medium text-text-primary">{item.subject}</h4>
            {item.textPreview ? <p className="mt-2 text-sm text-text-secondary">{item.textPreview}...</p> : null}
            {item.url ? (
              <a href={item.url} target="_blank" rel="noreferrer" className="mt-3 inline-block text-sm text-text-primary underline">
                View Gazette PDF
              </a>
            ) : null}
          </article>
        ))}
        {rows?.length === 0 ? <p className="text-sm text-text-secondary">No gazette data available.</p> : null}
      </div>
    </section>
  );
}
