import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { apiClient, type PolicyAnalysis, type PolicyListItem } from "../api/client";
import { useDocumentSelectionStore } from "../stores/documentSelectionStore";

type DocumentRow = {
  id: string;
  type: string;
  title: string;
  fileName: string;
  date: string;
  sector: string;
  status: string;
  aiStatus: string;
  sourceUrl?: string;
  rawContent?: string;
};

type ControlsForm = {
  search: string;
  filter: "All" | "Type" | "Sector";
  sort: "Date Desc" | "Date Asc" | "Status";
  status: "All" | "Reviewed" | "Unreviewed" | "Manual";
};

type RawPolicyModalState = {
  id: string;
  title: string;
  fileName: string;
  content: string;
};

const fadeUp = {
  hidden: { opacity: 0, y: 4 },
  show: { opacity: 1, y: 0 },
};

const sampleDocuments: DocumentRow[] = [
  { id: "D-1001", type: "Policy", title: "Cross-Border Retention Policy", fileName: "retention_policy_v2.pdf", date: "2026-02-20", sector: "Finance", status: "Reviewed", aiStatus: "Processed" },
  { id: "D-1002", type: "Directive", title: "Incident Reporting Directive", fileName: "incident_directive.docx", date: "2026-02-19", sector: "Healthcare", status: "Manual", aiStatus: "Manual" },
  { id: "D-1003", type: "Procedure", title: "Record Access Procedure", fileName: "record_access.xlsx", date: "2026-02-18", sector: "Public", status: "Unreviewed", aiStatus: "Queued" },
  { id: "D-1004", type: "Guideline", title: "Sanctions Screening Guideline", fileName: "screening_guideline.pdf", date: "2026-02-16", sector: "Energy", status: "Reviewed", aiStatus: "Processed" },
  { id: "D-1005", type: "Policy", title: "Vendor Due Diligence Policy", fileName: "vendor_due_diligence.pdf", date: "2026-02-15", sector: "Finance", status: "Manual", aiStatus: "Manual" },
  { id: "D-1006", type: "Directive", title: "Consumer Data Handling Directive", fileName: "consumer_data_directive.docx", date: "2026-02-14", sector: "Healthcare", status: "Reviewed", aiStatus: "Processed" },
  { id: "D-1007", type: "Procedure", title: "Escalation Procedure", fileName: "escalation_procedure.pdf", date: "2026-02-13", sector: "Public", status: "Unreviewed", aiStatus: "Queued" },
  { id: "D-1008", type: "Guideline", title: "Policy Harmonization Guideline", fileName: "harmonization_guideline.pdf", date: "2026-02-12", sector: "Energy", status: "Reviewed", aiStatus: "Processed" },
];

const rawPolicyContent: Record<string, string> = {
  "D-1001": "Section 1. Retention Horizon\nAll regulated records must be retained for seven years.\n\nSection 2. Retrieval SLA\nRequested records must be retrievable within 48 hours, including audit evidence.",
  "D-1002": "Section 1. Incident Disclosure\nAll material incidents require legal pre-review and final officer sign-off.\n\nSection 2. Notification Sequence\nNotify regulator channel within prescribed jurisdictional windows.",
  "D-1003": "Section 1. Access Procedure\nAll privileged access events must include reason code, approver, and timestamp.\n\nSection 2. Verification\nQuarterly control verification is mandatory.",
  "D-1004": "Section 1. Screening Rule\nCounterparty screening must run before final transaction authorization.\n\nSection 2. Escalation\nPotential sanctions matches must be escalated to legal ops immediately.",
  "D-1005": "Section 1. Due Diligence\nVendor onboarding requires sanctions, ownership, and litigation review.\n\nSection 2. Renewal\nRenewal controls must re-validate risk tier and evidence completeness.",
  "D-1006": "Section 1. Consumer Data Handling\nProcessing requires lawful basis tagging and retention clock assignment.\n\nSection 2. Deletion\nData deletion requests must be fulfilled with immutable audit entries.",
  "D-1007": "Section 1. Escalation Protocol\nCritical findings route to risk committee with 24-hour turnaround.\n\nSection 2. Recordkeeping\nEach escalation event must preserve chain-of-custody data.",
  "D-1008": "Section 1. Harmonization\nPolicy conflicts across regions must be mapped and normalized before publication.\n\nSection 2. Governance\nAll harmonized updates require legal and compliance co-signatures.",
};

function StatusTag({ status }: { status: DocumentRow["status"] }) {
  const className =
    status === "Reviewed"
      ? "font-medium text-text-primary"
      : status === "Manual"
        ? "italic text-text-secondary"
        : "text-text-secondary";

  return (
    <span className={["inline-flex rounded-full border border-border-primary bg-surface-primary px-3 py-1 text-xs", className].join(" ")}>
      {status}
    </span>
  );
}

export function DocumentListPage() {
  const navigate = useNavigate();
  const [rawPolicyModal, setRawPolicyModal] = useState<RawPolicyModalState | null>(null);
  const [documents, setDocuments] = useState<DocumentRow[]>(sampleDocuments);
  const [policyAnalyses, setPolicyAnalyses] = useState<PolicyAnalysis[]>([]);
  const [policyQuestions, setPolicyQuestions] = useState<Record<string, string>>({});
  const [policyAnswers, setPolicyAnswers] = useState<Record<string, string>>({});
  const [policyLoading, setPolicyLoading] = useState<Record<string, boolean>>({});

  const { register, watch, setValue } = useForm<ControlsForm>({
    defaultValues: {
      search: "",
      filter: "All",
      sort: "Date Desc",
      status: "All",
    },
  });

  const controls = watch();
  const [sorting, setSorting] = useState<SortingState>([{ id: "date", desc: true }]);

  useEffect(() => {
    let active = true;

    const mapPolicyToRow = (policy: PolicyListItem): DocumentRow => ({
      id: policy.id,
      type: "Policy",
      title: policy.title,
      fileName: `${policy.id}.txt`,
      date: policy.effectiveDate || new Date().toISOString().slice(0, 10),
      sector: policy.authority,
      status: policy.status || "Unreviewed",
      aiStatus: policy.status === "Processed" ? "Processed" : "Queued",
    });

    const mapGazetteToRow = (item: unknown, index: number): DocumentRow | null => {
      const record = typeof item === "object" && item !== null ? (item as Record<string, unknown>) : null;
      const id = String(record?.id ?? `gazette-${index}`);
      const subject = String(record?.subject ?? "").trim();
      const url = String(record?.url ?? "").trim();
      const text = String(record?.text ?? "").trim();

      if (!subject && !url) {
        return null;
      }

      return {
        id,
        type: "Gazette",
        title: subject || id,
        fileName: id,
        date: new Date().toISOString().slice(0, 10),
        sector: "Government",
        status: "Reviewed",
        aiStatus: "Processed",
        sourceUrl: url || undefined,
        rawContent: text || undefined,
      };
    };

    const loadDocuments = async () => {
      try {
        const [policiesResult, gazettesResult] = await Promise.all([
          apiClient.getPolicies().catch(() => [] as PolicyListItem[]),
          apiClient.getGazettes().catch(() => [] as unknown),
        ]);

        const policyRows = policiesResult.map(mapPolicyToRow);
        const gazetteRows = Array.isArray(gazettesResult)
          ? gazettesResult
              .map(mapGazetteToRow)
              .filter((item): item is DocumentRow => item !== null)
          : [];

        const merged = [...policyRows, ...gazetteRows];

        if (active) {
          setDocuments(merged.length > 0 ? merged : sampleDocuments);
        }
      } catch {
        if (active) {
          setDocuments(sampleDocuments);
        }
      }
    };

    void loadDocuments();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    const loadPolicyAnalyses = async () => {
      try {
        const response = await apiClient.getPolicyAnalyses();
        if (active) {
          setPolicyAnalyses(Array.isArray(response) ? response : []);
        }
      } catch {
        if (active) {
          setPolicyAnalyses([]);
        }
      }
    };

    void loadPolicyAnalyses();
    return () => {
      active = false;
    };
  }, []);

  const { selectedIds, setSelected, setManySelected, clearSelected } = useDocumentSelectionStore();

  const filteredRows = useMemo(() => {
    const search = controls.search.trim().toLowerCase();

    return documents.filter((row) => {
      const textPass =
        search.length === 0 ||
        row.title.toLowerCase().includes(search) ||
        row.fileName.toLowerCase().includes(search) ||
        row.type.toLowerCase().includes(search);

      const statusPass = controls.status === "All" || row.status === controls.status;
      return textPass && statusPass;
    });
  }, [controls.search, controls.status, documents]);

  const selectedCount = useMemo(
    () => filteredRows.filter((row) => selectedIds[row.id]).length,
    [filteredRows, selectedIds]
  );

  const allVisibleSelected = filteredRows.length > 0 && filteredRows.every((row) => selectedIds[row.id]);

  const openDocument = (row: DocumentRow) => {
    navigate(`/documents/analysis/${row.id}`);
  };

  const openRawPolicy = async (row: DocumentRow) => {
    if (row.rawContent || row.sourceUrl) {
      const content = row.rawContent ?? (row.sourceUrl ? `View Gazette PDF:\n${row.sourceUrl}` : "No policy text available.");
      setRawPolicyModal({ id: row.id, title: row.title, fileName: row.fileName, content });
      return;
    }

    setRawPolicyModal({ id: row.id, title: row.title, fileName: row.fileName, content: "Loading policy content..." });
    try {
      const detail = await apiClient.getPolicyById(row.id);
      setRawPolicyModal({ id: row.id, title: row.title, fileName: row.fileName, content: detail.content || "No policy text available." });
    } catch {
      setRawPolicyModal({ id: row.id, title: row.title, fileName: row.fileName, content: rawPolicyContent[row.id] ?? "Raw policy text is not available for this document." });
    }
  };

  const columns = useMemo<ColumnDef<DocumentRow>[]>(
    () => [
      {
        id: "select",
        header: () => (
          <input
            type="checkbox"
            aria-label="Select all documents"
            checked={allVisibleSelected}
            onChange={(event) => setManySelected(filteredRows.map((row) => row.id), event.target.checked)}
            className="h-4 w-4 rounded border-border-primary bg-bg-secondary"
          />
        ),
        cell: ({ row }) => (
          <input
            type="checkbox"
            aria-label={`Select ${row.original.title}`}
            checked={Boolean(selectedIds[row.original.id])}
            onChange={(event) => setSelected(row.original.id, event.target.checked)}
            className="h-4 w-4 rounded border-border-primary bg-bg-secondary"
          />
        ),
        enableSorting: false,
      },
      { accessorKey: "type", header: "Type" },
      {
        accessorKey: "title",
        header: "Title",
        cell: ({ row }) => (
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              openDocument(row.original);
            }}
            className="text-left font-medium text-text-primary hover:underline"
          >
            {row.original.title}
          </button>
        ),
      },
      {
        accessorKey: "fileName",
        header: "File Name",
        cell: ({ row }) => (
          <button
            type="button"
            onClick={() => openDocument(row.original)}
            className="text-left text-text-primary hover:underline"
          >
            {row.original.fileName}
          </button>
        ),
      },
      { accessorKey: "date", header: "Date" },
      { accessorKey: "sector", header: "Sector" },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => <StatusTag status={row.original.status} />,
      },
      {
        accessorKey: "aiStatus",
        header: "AI Processing",
        cell: ({ row }) => <span className="text-sm text-text-secondary">{row.original.aiStatus}</span>,
      },
    ],
    [allVisibleSelected, filteredRows, selectedIds, setManySelected, setSelected]
  );

  const table = useReactTable({
    data: filteredRows,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 6 } },
  });

  const setSortFromControl = (value: ControlsForm["sort"]) => {
    setValue("sort", value);
    if (value === "Date Desc") {
      setSorting([{ id: "date", desc: true }]);
    } else if (value === "Date Asc") {
      setSorting([{ id: "date", desc: false }]);
    } else {
      setSorting([{ id: "status", desc: false }]);
    }
  };

  const askAboutRegulation = async (item: PolicyAnalysis) => {
    const gazetteId = item?.gazette_id ?? "";
    if (!gazetteId) {
      return;
    }

    const question = (policyQuestions[gazetteId] ?? "").trim() || "Does this regulation affect banking?";

    setPolicyLoading((prev) => ({ ...prev, [gazetteId]: true }));
    try {
      const response = await apiClient.queryPolicy({ question, gazette_id: gazetteId });
      const answer = response?.answer ?? response?.error ?? "No verified information found in available gazette records.";
      setPolicyAnswers((prev) => ({ ...prev, [gazetteId]: answer }));
    } catch {
      setPolicyAnswers((prev) => ({ ...prev, [gazetteId]: "No verified information found in available gazette records." }));
    } finally {
      setPolicyLoading((prev) => ({ ...prev, [gazetteId]: false }));
    }
  };

  const riskBadgeClass = (riskLevel: string | null | undefined) => {
    const normalized = (riskLevel ?? "").toLowerCase();
    if (normalized === "high") {
      return "border-border-primary bg-surface-elevated text-text-primary";
    }
    if (normalized === "medium") {
      return "border-border-soft bg-surface-primary text-text-primary";
    }
    return "border-border-soft bg-bg-secondary text-text-secondary";
  };

  return (
    <div className="mx-auto w-full max-w-[1280px] px-8 pb-20 pt-12">
      <motion.section initial="hidden" animate="show" variants={fadeUp} transition={{ duration: 0.22 }} className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-[0.1em] text-text-muted">Documents</p>
        <h2 className="mt-4 text-[40px] font-semibold tracking-tight text-text-primary md:text-5xl">Document Registry</h2>
        <p className="mt-4 max-w-4xl text-base leading-8 text-text-secondary">
          Centralized repository of regulatory policies, workflow states, and processing integrity.
        </p>
      </motion.section>

      <motion.section initial="hidden" animate="show" variants={fadeUp} transition={{ duration: 0.22 }} className="mb-6 flex flex-wrap items-center justify-between gap-6">
        {policyAnalyses?.length > 0 ? (
          <section className="mb-10 w-full" aria-label="Regulations Intelligence">
            <div className="mb-4">
              <h3 className="text-base font-semibold text-text-primary">Regulations Intelligence</h3>
              <p className="mt-1 text-xs text-text-secondary">Structured LLM analysis from gazette records.</p>
            </div>

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
              {policyAnalyses?.slice(0, 8).map((item) => {
                const gazetteId = item?.gazette_id ?? "";
                const policyName = item?.analysis?.policy_name ?? item?.subject ?? "Unnamed regulation";
                const ministry = item?.analysis?.ministry ?? "Unknown ministry";
                const effectiveDate = item?.analysis?.effective_date ?? "N/A";
                const riskLevel = item?.analysis?.risk_level ?? "Low";
                const industries = item?.analysis?.industries_impacted ?? [];
                const actions = item?.analysis?.compliance_actions_required ?? [];

                return (
                  <article key={gazetteId || policyName} className="rounded-md border border-border-primary bg-surface-card p-4">
                    <div className="flex items-start justify-between gap-3">
                      <h4 className="text-sm font-semibold text-text-primary">{policyName}</h4>
                      <span className={["inline-flex rounded-full border px-2 py-0.5 text-xs font-medium", riskBadgeClass(riskLevel)].join(" ")}>
                        {riskLevel}
                      </span>
                    </div>

                    <p className="mt-2 text-xs text-text-secondary">Ministry: {ministry}</p>
                    <p className="mt-1 text-xs text-text-secondary">Effective Date: {effectiveDate}</p>
                    <p className="mt-3 text-xs font-medium text-text-primary">Industries Impacted</p>
                    <p className="mt-1 text-sm text-text-secondary">{industries?.length > 0 ? industries.join(", ") : "Not specified"}</p>
                    <p className="mt-3 text-xs font-medium text-text-primary">Compliance Actions</p>
                    <p className="mt-1 text-sm text-text-secondary">{actions?.length > 0 ? actions.join("; ") : "Not specified"}</p>

                    <div className="mt-4 flex flex-col gap-2">
                      <input
                        type="text"
                        value={policyQuestions[gazetteId] ?? ""}
                        onChange={(event) =>
                          setPolicyQuestions((prev) => ({
                            ...prev,
                            [gazetteId]: event.target.value,
                          }))
                        }
                        placeholder="Ask a compliance question"
                        className="h-10 w-full rounded-md border border-border-soft bg-bg-secondary px-3 text-sm text-text-primary placeholder:text-text-muted focus:border-border-primary focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => void askAboutRegulation(item)}
                        disabled={Boolean(policyLoading[gazetteId])}
                        className="inline-flex h-10 items-center justify-center rounded-md border border-border-primary bg-surface-elevated px-3 text-sm text-text-primary disabled:opacity-50"
                      >
                        Ask About This Regulation
                      </button>
                      {policyAnswers[gazetteId] ? <p className="text-sm text-text-secondary">{policyAnswers[gazetteId]}</p> : null}
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
        ) : null}

        <div className="w-full max-w-[420px]">
          <input
            {...register("search")}
            type="search"
            placeholder="Search title, file name, type"
            className="h-11 w-full rounded-md border border-border-soft bg-bg-secondary px-4 text-sm text-text-primary placeholder:text-text-muted focus:border-border-primary focus:outline-none"
          />
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <select
            {...register("filter")}
            className="h-11 rounded-md border border-border-soft bg-bg-secondary px-3 text-sm text-text-secondary focus:border-border-primary focus:outline-none"
          >
            <option>All</option>
            <option>Type</option>
            <option>Sector</option>
          </select>

          <select
            value={controls.sort}
            onChange={(event) => setSortFromControl(event.target.value as ControlsForm["sort"])}
            className="h-11 rounded-md border border-border-soft bg-bg-secondary px-3 text-sm text-text-secondary focus:border-border-primary focus:outline-none"
          >
            <option>Date Desc</option>
            <option>Date Asc</option>
            <option>Status</option>
          </select>

        </div>
      </motion.section>

      <motion.section initial="hidden" animate="show" variants={fadeUp} transition={{ duration: 0.22 }} className="mb-8 flex flex-wrap gap-4">
        {(["All", "Reviewed", "Unreviewed", "Manual"] as const).map((chip) => {
          const active = controls.status === chip;
          return (
            <button
              key={chip}
              type="button"
              onClick={() => setValue("status", chip)}
              className={[
                "rounded-full border px-4 py-2 text-sm",
                active
                  ? "border-border-primary bg-surface-elevated text-text-primary"
                  : "border-border-primary bg-surface-primary text-text-muted hover:bg-surface-elevated",
              ].join(" ")}
            >
              {chip}
            </button>
          );
        })}
      </motion.section>

      <motion.section initial="hidden" animate="show" variants={fadeUp} transition={{ duration: 0.23 }}>
        {selectedCount > 0 ? (
          <div className="mb-4 flex items-center justify-between rounded-xl border border-border-primary bg-surface-elevated px-4 py-3">
            <p className="text-sm text-text-primary">{selectedCount} selected</p>
            <div className="flex items-center gap-3">
              <button type="button" className="rounded-md border border-border-primary px-3 py-1.5 text-xs text-text-primary hover:bg-surface-card">Assign</button>
              <button type="button" className="rounded-md border border-border-primary px-3 py-1.5 text-xs text-text-primary hover:bg-surface-card">Mark Reviewed</button>
              <button type="button" onClick={clearSelected} className="rounded-md border border-border-primary px-3 py-1.5 text-xs text-text-primary hover:bg-surface-card">Clear</button>
            </div>
          </div>
        ) : null}

        <div className="overflow-hidden rounded-md border border-border-primary bg-surface-card">
          <div className="min-h-[420px] overflow-x-auto">
            <table className="hidden w-full border-collapse md:table">
              <thead className="bg-bg-secondary">
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr key={headerGroup.id}>
                    {headerGroup.headers.map((header) => {
                      const headerLabel = flexRender(header.column.columnDef.header, header.getContext());
                      const responsiveClass =
                        header.column.id === "sector" || header.column.id === "fileName"
                          ? "hidden xl:table-cell"
                          : "table-cell";

                      return (
                        <th
                          key={header.id}
                          className={[
                            "border-b border-border-soft px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.08em] text-text-muted",
                            responsiveClass,
                          ].join(" ")}
                        >
                          {header.column.getCanSort() ? (
                            <button
                              type="button"
                              onClick={header.column.getToggleSortingHandler()}
                              className="inline-flex items-center gap-1"
                            >
                              <span>{headerLabel}</span>
                            </button>
                          ) : (
                            headerLabel
                          )}
                        </th>
                      );
                    })}
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows.map((row) => (
                  <motion.tr
                    key={row.id}
                    whileHover={{ opacity: 0.96 }}
                    className="h-14 border-b border-border-soft hover:bg-surface-elevated/60"
                  >
                    {row.getVisibleCells().map((cell) => {
                      const responsiveClass =
                        cell.column.id === "sector" || cell.column.id === "fileName"
                          ? "hidden xl:table-cell"
                          : "table-cell";

                      return (
                        <td key={cell.id} className={["px-4 py-3 text-sm text-text-secondary", responsiveClass].join(" ")}>
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </td>
                      );
                    })}
                  </motion.tr>
                ))}
              </tbody>
            </table>

            <div className="space-y-4 p-4 md:hidden">
              {table.getRowModel().rows.map((row) => (
                <article
                  key={row.id}
                  className="rounded-md border border-border-soft bg-surface-primary p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <button
                        type="button"
                        onClick={() => openDocument(row.original)}
                        className="text-left text-sm font-medium text-text-primary hover:underline"
                      >
                        {row.original.title}
                      </button>
                      <p className="mt-1 text-xs text-text-muted">{row.original.type} • {row.original.date}</p>
                    </div>
                    <StatusTag status={row.original.status} />
                  </div>
                  <button
                    type="button"
                    onClick={() => openRawPolicy(row.original)}
                    className="mt-3 text-left text-xs text-text-primary hover:underline"
                  >
                    {row.original.fileName}
                  </button>
                </article>
              ))}
            </div>
          </div>

        </div>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
          {(() => {
            const pageIndex = table.getState().pagination.pageIndex;
            const pageSize = table.getState().pagination.pageSize;
            const currentCount = table.getRowModel().rows.length;
            const totalCount = filteredRows.length;
            const start = totalCount === 0 ? 0 : pageIndex * pageSize + 1;
            const end = totalCount === 0 ? 0 : pageIndex * pageSize + currentCount;

            return (
              <p className="text-sm text-text-secondary">
                Showing {start}–{end} of {totalCount}
              </p>
            );
          })()}

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="rounded-md border border-border-primary px-3 py-1.5 text-xs text-text-primary disabled:opacity-40"
            >
              Previous
            </button>

            {Array.from({ length: table.getPageCount() }, (_, index) => (
              <button
                key={index}
                type="button"
                onClick={() => table.setPageIndex(index)}
                className={[
                  "rounded-md border border-border-primary px-3 py-1.5 text-xs",
                  table.getState().pagination.pageIndex === index
                    ? "bg-surface-elevated text-text-primary"
                    : "text-text-secondary",
                ].join(" ")}
              >
                {index + 1}
              </button>
            ))}

            <button
              type="button"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="rounded-md border border-border-primary px-3 py-1.5 text-xs text-text-primary disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>

      </motion.section>

      {rawPolicyModal ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-bg-primary/80 px-4" role="dialog" aria-modal="true" aria-label="Raw policy viewer">
          <section className="w-full max-w-3xl rounded-md border border-border-primary bg-surface-card p-8">
            <header className="flex items-start justify-between gap-4 border-b border-border-soft pb-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-text-muted">Raw Policy</p>
                <h3 className="mt-2 text-xl font-semibold text-text-primary">{rawPolicyModal.title}</h3>
                <p className="mt-1 text-sm text-text-secondary">{rawPolicyModal.fileName}</p>
              </div>
              <button
                type="button"
                onClick={() => setRawPolicyModal(null)}
                className="rounded-md border border-border-primary px-3 py-1.5 text-xs text-text-primary hover:bg-surface-elevated"
              >
                Close
              </button>
            </header>

            <div className="mt-6 max-h-[420px] overflow-y-auto rounded-md border border-border-soft bg-surface-primary p-6">
              <pre className="whitespace-pre-wrap text-sm leading-7 text-text-secondary">
                {rawPolicyModal.content}
              </pre>
            </div>
          </section>
        </div>
      ) : null}
    </div>
  );
}
