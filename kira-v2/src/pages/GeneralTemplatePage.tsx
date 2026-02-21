import { animate, motion } from "framer-motion";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { apiClient, type DashboardSummaryResponse } from "../api/client";

type KpiItem = {
  label: string;
  value: number;
  subtext: string;
};

type DocTypeMetric = {
  type: string;
  count: number;
  trend: number[];
};

type StatusMetric = {
  label: string;
  value: number;
};

const kpiData: KpiItem[] = [
  { label: "Total Documents", value: 1240, subtext: "↑ Intake baseline reached" },
  { label: "Assigned", value: 860, subtext: "↑ Routed to owners" },
  { label: "Reviewed", value: 610, subtext: "↑ Reviewed this cycle" },
  { label: "Unreviewed / Pending", value: 250, subtext: "↑ Pending queue" },
];

const totalDocuments = kpiData[0].value;

const assignedByType: DocTypeMetric[] = [
  { type: "Contracts", count: 310, trend: [68, 71, 70, 74, 76, 78] },
  { type: "Policies", count: 240, trend: [56, 57, 60, 62, 63, 64] },
  { type: "Licensing", count: 180, trend: [41, 45, 47, 48, 50, 51] },
  { type: "Filings", count: 130, trend: [32, 33, 34, 36, 37, 38] },
];

const reviewedByType: Omit<DocTypeMetric, "trend">[] = [
  { type: "Contracts", count: 190 },
  { type: "Policies", count: 170 },
  { type: "Licensing", count: 140 },
  { type: "Filings", count: 110 },
];

const processStatus: StatusMetric[] = [
  { label: "Complete", value: 52 },
  { label: "Incomplete", value: 21 },
  { label: "Secure", value: 19 },
  { label: "Unreadable", value: 8 },
];

const ocrQuality: StatusMetric[] = [
  { label: "B", value: 46 },
  { label: "C", value: 29 },
  { label: "D", value: 17 },
  { label: "E & F", value: 8 },
];

const fadeUp = {
  hidden: { opacity: 0, y: 4 },
  show: { opacity: 1, y: 0 },
};

const chartTones = ["var(--text-primary)", "var(--text-secondary)", "var(--text-muted)", "var(--text-disabled)"];

function CountUp({ value }: { value: number }) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    const controls = animate(0, value, {
      duration: 0.8,
      ease: "easeOut",
      onUpdate: (latest) => setDisplayValue(Math.round(latest)),
    });

    return () => controls.stop();
  }, [value]);

  const formatted = useMemo(() => displayValue.toLocaleString(), [displayValue]);
  return <p className="text-[42px] font-semibold leading-none text-text-primary">{formatted}</p>;
}

function DashboardCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section aria-label={title} className="flex h-full flex-col gap-6 rounded-md border border-border-primary bg-surface-card p-8">
      <h2 className="text-[32px] font-semibold leading-none text-text-primary">{title}</h2>
      {children}
    </section>
  );
}

function MonochromeTooltipContent({ active, payload, label }: { active?: boolean; payload?: Array<{ value?: number | string; name?: string; dataKey?: string; payload?: { label?: string; type?: string } }>; label?: string | number }) {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  const first = payload[0];
  const value = first.value ?? "-";

  const candidateName =
    first.payload?.type ??
    first.payload?.label ??
    (typeof first.name === "string" && first.name.toLowerCase() !== "count" ? first.name : undefined) ??
    (typeof label === "string" || typeof label === "number" ? String(label) : undefined) ??
    "Unknown";

  return (
    <div className="rounded-md border border-border-primary bg-surface-card px-4 py-3 text-text-primary">
      <p className="text-sm font-medium text-text-primary">{candidateName}</p>
      <p className="mt-2 text-sm font-semibold text-text-primary">count: {String(value)}</p>
    </div>
  );
}

function MonochromeTooltip({ position }: { position?: { x: number; y: number } }) {
  return (
    <Tooltip
      content={<MonochromeTooltipContent />}
      wrapperStyle={{ outline: "none" }}
      position={position}
      cursor={{ fill: "var(--bg-secondary)", opacity: 0.5 }}
    />
  );
}

function KpiRadialWidget({ item }: { item: KpiItem }) {
  const percentage = Math.round((item.value / totalDocuments) * 100);

  return (
    <section aria-label={item.label} className="col-span-12 min-h-[260px] overflow-hidden rounded-md border border-border-primary bg-surface-card p-8 md:col-span-6 xl:col-span-3">
      <div className="flex flex-col items-center gap-4">
        <div className="relative flex h-[160px] w-[160px] items-center justify-center" role="img" aria-label={`${item.label} progress ring ${percentage} percent`}>
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart data={[{ value: percentage }]} innerRadius="84%" outerRadius="100%" startAngle={90} endAngle={-270}>
              <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
              <RadialBar dataKey="value" cornerRadius={10} background={{ fill: "var(--border-soft)" }} fill="var(--text-primary)" />
            </RadialBarChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <CountUp value={item.value} />
          </div>
        </div>
        <p className="text-center text-sm font-medium text-text-muted">{item.label}</p>
        <p className="text-center text-sm text-text-secondary">{percentage}% of total</p>
        <p className="text-center text-sm text-text-secondary">{item.subtext}</p>
      </div>
    </section>
  );
}

function AssignedRows({ data }: { data: DocTypeMetric[] }) {
  const max = Math.max(...data.map((item) => item.count));

  return (
    <div className="h-[340px] w-full" role="img" aria-label="Assigned documents by type with proportional bars and trend spark lines">
      <div className="flex h-full flex-col justify-between gap-6">
        {data.map((item) => (
          <div key={item.type} className="grid grid-cols-[120px_1fr_56px_96px] items-center gap-4">
            <p className="text-sm text-text-secondary">{item.type}</p>
            <div className="h-3 rounded-full bg-bg-secondary">
              <div className="h-3 rounded-full bg-text-primary" style={{ width: `${(item.count / max) * 100}%` }} />
            </div>
            <p className="text-right text-sm font-medium text-text-primary">{item.count}</p>
            <div className="h-8">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={item.trend.map((value, index) => ({ index, value }))}>
                  <Line type="monotone" dataKey="value" stroke="var(--text-secondary)" strokeWidth={1.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ProcessStatusDonut({ data }: { data: StatusMetric[] }) {
  const completion = 64;

  return (
    <div className="flex h-full flex-col items-center justify-between" role="img" aria-label="Process status donut chart showing overall completion">
      <div className="relative h-[280px] w-full max-w-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="label" innerRadius={74} outerRadius={108} stroke="var(--surface-card)" strokeWidth={2}>
              {data.map((entry, index) => (
                <Cell key={entry.label} fill={chartTones[index]} />
              ))}
            </Pie>
            <MonochromeTooltip position={{ x: 12, y: 12 }} />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <p className="text-xs uppercase tracking-[0.08em] text-text-muted">Completion</p>
          <p className="mt-2 text-4xl font-semibold text-text-primary">{completion}%</p>
        </div>
      </div>

      <div className="mt-4 grid w-full grid-cols-2 gap-x-6 gap-y-3">
        {data.map((item, index) => (
          <div key={item.label} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: chartTones[index] }} />
              <span className="text-text-secondary">{item.label}</span>
            </div>
            <span className="font-medium text-text-primary">{item.value}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function OcrStackedDistribution({ data }: { data: StatusMetric[] }) {
  return (
    <div className="space-y-6" role="img" aria-label="OCR quality stacked distribution for grades B, C, D, and E and F">
      <div className="mb-6 flex h-10 w-full overflow-hidden rounded-md border border-border-soft bg-bg-secondary">
        {data.map((item, index) => (
          <div key={item.label} className="h-10" style={{ width: `${item.value}%`, backgroundColor: chartTones[index] }} aria-hidden="true" />
        ))}
      </div>

      <div className="space-y-3">
        {data.map((item, index) => (
          <div key={item.label} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: chartTones[index] }} />
              <span className="text-text-secondary">Grade {item.label}</span>
            </div>
            <span className="font-medium text-text-primary">{item.value}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function GeneralTemplatePage() {
  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const response = await apiClient.getDashboard();
        if (active) {
          setSummary(response);
        }
      } catch {
        if (active) {
          setSummary(null);
        }
      }
    };

    void load();
    return () => {
      active = false;
    };
  }, []);

  const dashboardKpis: KpiItem[] = summary
    ? [
        { label: "Total Documents", value: summary.totalDocuments, subtext: "Synced from backend" },
        { label: "Assigned", value: summary.assignedPolicies, subtext: "Synced from backend" },
        { label: "Reviewed", value: summary.reviewedPolicies, subtext: "Synced from backend" },
        { label: "Unreviewed / Pending", value: summary.pendingPolicies, subtext: "Synced from backend" },
      ]
    : kpiData;

  const dashboardAssigned: DocTypeMetric[] = summary
    ? summary.documentsByType.slice(0, 4).map((item) => ({ type: item.type, count: item.count, trend: [1, 1, 1, 1, 1, 1] }))
    : assignedByType;

  const dashboardReviewed = summary
    ? summary.documentsByType.slice(0, 4).map((item) => ({ type: item.type, count: item.count }))
    : reviewedByType;

  const dashboardProcessStatus: StatusMetric[] = summary
    ? summary.processingStatus.map((item) => ({
        label: item.status,
        value: summary.totalDocuments > 0 ? Math.round((item.count / summary.totalDocuments) * 100) : 0,
      }))
    : processStatus;

  return (
    <div className="mx-auto w-full max-w-[1280px] pb-20">
        <motion.section initial="hidden" animate="show" variants={fadeUp} transition={{ duration: 0.24 }} className="mb-12">
          <p className="text-xs font-semibold uppercase tracking-[0.1em] text-text-muted">Dashboard</p>
          <h2 className="mt-4 text-[40px] font-semibold tracking-tight text-text-primary md:text-5xl">Regulatory Operations Overview</h2>
          <p className="mt-4 max-w-4xl text-base leading-8 text-text-secondary">
            Real-time monitoring of document intake, workflow status, and OCR integrity.
          </p>
        </motion.section>

        <motion.section
          className="mt-12 grid grid-cols-12 gap-8"
          initial="hidden"
          animate="show"
          variants={{ hidden: {}, show: { transition: { staggerChildren: 0.05 } } }}
        >
          {dashboardKpis.map((item) => (
            <motion.div key={item.label} variants={fadeUp} transition={{ duration: 0.24 }} className="col-span-12 md:col-span-6 xl:col-span-3">
              <KpiRadialWidget item={item} />
            </motion.div>
          ))}
        </motion.section>

        <motion.section className="mt-16 grid grid-cols-12 gap-8" initial="hidden" animate="show" variants={fadeUp} transition={{ duration: 0.26 }}>
            <div className="col-span-12 lg:col-span-8">
            <DashboardCard title="Assigned Documents by Type">
              <AssignedRows data={dashboardAssigned} />
            </DashboardCard>
          </div>

            <div className="col-span-12 lg:col-span-4">
            <DashboardCard title="Process Status">
              <ProcessStatusDonut data={dashboardProcessStatus} />
            </DashboardCard>
          </div>
        </motion.section>

        <motion.section className="mt-16 grid grid-cols-12 gap-8" initial="hidden" animate="show" variants={fadeUp} transition={{ duration: 0.28 }}>
          <div className="col-span-12 lg:col-span-8">
            <DashboardCard title="Reviewed Documents by Type">
              <div className="h-[340px] w-full" role="img" aria-label="Vertical bar chart showing reviewed documents by type: Contracts 190, Policies 170, Licensing 140, Filings 110">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={dashboardReviewed} margin={{ top: 8, right: 8, left: 0, bottom: 8 }} barSize={48} barGap={24}>
                    <CartesianGrid stroke="var(--border-soft)" strokeDasharray="2 6" vertical={false} />
                    <XAxis dataKey="type" tick={{ fill: "var(--text-secondary)", fontSize: 12 }} axisLine={{ stroke: "var(--border-primary)" }} tickLine={false} />
                    <YAxis tick={{ fill: "var(--text-secondary)", fontSize: 12 }} axisLine={{ stroke: "var(--border-primary)" }} tickLine={false} />
                    <MonochromeTooltip />
                    <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                      {dashboardReviewed.map((entry, index) => (
                        <Cell key={entry.type} fill={chartTones[index]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </DashboardCard>
          </div>

          <div className="col-span-12 lg:col-span-4">
            <DashboardCard title="OCR Quality Distribution">
              <OcrStackedDistribution data={ocrQuality} />
            </DashboardCard>
          </div>
        </motion.section>
      </div>
  );
}
