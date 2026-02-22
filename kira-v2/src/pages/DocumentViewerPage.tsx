import * as Collapsible from "@radix-ui/react-collapsible";
import * as Tabs from "@radix-ui/react-tabs";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useParams } from "react-router-dom";
import { apiClient, ApiError, DEFAULT_ORG_PROFILE, type AnalysisRunResponse } from "../api/client";

const fadeUp = {
  hidden: { opacity: 0, y: 4 },
  show: { opacity: 1, y: 0 },
};

const chartTones = ["var(--text-primary)", "var(--text-secondary)", "var(--text-muted)", "var(--text-disabled)"];

const departmentImpact = [
  { name: "Legal", value: 82 },
  { name: "Risk", value: 74 },
  { name: "Operations", value: 61 },
  { name: "IT", value: 48 },
];

const workforceTrend = [
  { month: "Jan", value: 22 },
  { month: "Feb", value: 24 },
  { month: "Mar", value: 27 },
  { month: "Apr", value: 31 },
  { month: "May", value: 29 },
  { month: "Jun", value: 34 },
];

const riskTrend = [
  { week: "W1", value: 48 },
  { week: "W2", value: 54 },
  { week: "W3", value: 51 },
  { week: "W4", value: 63 },
  { week: "W5", value: 58 },
  { week: "W6", value: 66 },
];

const impactDistribution = [
  { group: "High", value: 26 },
  { group: "Medium", value: 49 },
  { group: "Low", value: 25 },
];

const severityBreakdown = [
  { name: "Critical", value: 16 },
  { name: "Moderate", value: 41 },
  { name: "Minor", value: 43 },
];

function MonoTooltip({
  formatter,
  labelFormatter,
}: {
  formatter?: (value: number, name: string) => [string, string] | string;
  labelFormatter?: (label: string) => string;
}) {
  return (
    <Tooltip
      contentStyle={{
        backgroundColor: "var(--surface-card)",
        border: "1px solid var(--border-primary)",
        borderRadius: "12px",
        color: "var(--text-primary)",
      }}
      itemStyle={{ color: "var(--text-primary)" }}
      labelStyle={{ color: "var(--text-primary)" }}
      wrapperStyle={{ color: "var(--text-primary)" }}
      cursor={{ fill: "var(--bg-secondary)", opacity: 0.4 }}
      formatter={
        formatter
          ? (value, name) => formatter(Number(value), String(name))
          : undefined
      }
      labelFormatter={
        labelFormatter
          ? (label) => labelFormatter(String(label))
          : undefined
      }
    />
  );
}

function ClauseBlock({ title, content }: { title: string; content: string }) {
  return (
    <Collapsible.Root className="rounded-md border border-border-soft bg-surface-primary">
      <Collapsible.Trigger className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-text-primary">
        <span>{title}</span>
        <span className="text-text-muted">Expand</span>
      </Collapsible.Trigger>
      <Collapsible.Content className="border-t border-border-soft px-4 py-3 text-sm leading-6 text-text-secondary">
        {content}
      </Collapsible.Content>
    </Collapsible.Root>
  );
}

function AnalysisTab({ analysisResult, analysisError }: { analysisResult: AnalysisRunResponse | null; analysisError: string | null }) {
  const relevantPolicies = analysisResult?.relevantPolicies ?? [];

  return (
    <div className="space-y-6">
      <section>
        <h3 className="text-lg font-semibold text-text-primary">Executive Summary</h3>
        <p className="mt-4 text-sm leading-6 text-text-secondary">
          {analysisResult?.impactSummary ?? "Loading analysis from backend..."}
        </p>
        {analysisError ? <p className="mt-2 text-xs text-text-muted">{analysisError}</p> : null}

        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {(relevantPolicies.length > 0 ? relevantPolicies : [{ id: "N/A", impactLevel: "Low" as const }]).slice(0, 3).map((item) => (
            <div key={item.id} className="rounded-md border border-border-primary bg-surface-elevated px-3 py-2 text-xs font-medium text-text-primary">
              {item.impactLevel} Priority: {item.id}
            </div>
          ))}
        </div>
      </section>

      <section>
        <h3 className="text-lg font-semibold text-text-primary">Key Clauses Extracted</h3>
        <div className="mt-4 space-y-3">
          <ClauseBlock title="Clause 4.2 — Retention Horizon" content="Records for regulated interactions must be retained for 7 years and made retrievable within 48 hours upon regulator request." />
          <ClauseBlock title="Clause 6.1 — Disclosure Protocol" content="Mandatory disclosure workflow must include legal review, regional counsel sign-off, and immutable audit logging." />
        </div>
      </section>

      <section>
        <h3 className="text-lg font-semibold text-text-primary">Compliance Requirements</h3>
        <p className="mt-4 text-sm leading-6 text-text-secondary">
          {analysisResult?.financialImpactProjection ?? "Financial projection will be available once analysis is complete."}
        </p>
      </section>

      <section>
        <h3 className="text-lg font-semibold text-text-primary">Risk Observations</h3>
        <p className="mt-4 text-sm leading-6 text-text-secondary">
          Current process has <span className="rounded border border-border-primary bg-surface-elevated px-1.5 py-0.5 font-medium text-text-primary">moderate exposure</span> due to manual clause classification
          and uneven department-level verification throughput.
        </p>
      </section>
    </div>
  );
}

function ImpactTab({ analysisResult }: { analysisResult: AnalysisRunResponse | null }) {
  const riskScore = analysisResult?.riskScore ?? 73;

  return (
    <div className="space-y-6">
      <section className="rounded-md border border-border-soft bg-surface-primary p-6">
        <h3 className="text-base font-semibold text-text-primary">Risk Score</h3>
        <div className="mt-4 flex items-center gap-6">
          <div className="h-24 w-24">
            <ResponsiveContainer width="100%" height="100%">
              <RadialBarChart data={[{ value: riskScore }]} innerRadius="72%" outerRadius="100%" startAngle={90} endAngle={-270}>
                <RadialBar dataKey="value" fill="var(--text-primary)" background={{ fill: "var(--border-soft)" }} />
              </RadialBarChart>
            </ResponsiveContainer>
          </div>
          <div>
            <p className="text-4xl font-semibold text-text-primary">{riskScore}</p>
            <p className="mt-1 text-sm text-text-secondary">Elevated monitoring required</p>
          </div>
        </div>
      </section>

      <section className="rounded-md border border-border-soft bg-surface-primary p-6">
        <h3 className="text-base font-semibold text-text-primary">Department Impact Matrix</h3>
        <div className="mt-4 h-[280px] w-full" role="img" aria-label="Department impact horizontal bar chart">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={departmentImpact} layout="vertical" margin={{ top: 8, right: 12, left: 10, bottom: 8 }}>
              <CartesianGrid stroke="var(--border-soft)" strokeDasharray="2 6" horizontal={false} />
              <XAxis type="number" tick={{ fill: "var(--text-muted)", fontSize: 12 }} axisLine={{ stroke: "var(--border-primary)" }} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fill: "var(--text-secondary)", fontSize: 12 }} axisLine={{ stroke: "var(--border-primary)" }} tickLine={false} width={96} />
              <MonoTooltip />
              <Bar dataKey="value" fill="var(--text-primary)" radius={[4, 4, 4, 4]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="rounded-md border border-border-soft bg-surface-primary p-6">
        <h3 className="text-base font-semibold text-text-primary">Workforce Prediction Metrics</h3>
        <div className="mt-4 h-[280px] w-full" role="img" aria-label="Workforce prediction line chart">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={workforceTrend} margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
              <CartesianGrid stroke="var(--border-soft)" strokeDasharray="2 6" />
              <XAxis dataKey="month" tick={{ fill: "var(--text-muted)", fontSize: 12 }} axisLine={{ stroke: "var(--border-primary)" }} tickLine={false} />
              <YAxis tick={{ fill: "var(--text-muted)", fontSize: 12 }} axisLine={{ stroke: "var(--border-primary)" }} tickLine={false} width={36} />
              <MonoTooltip />
              <Line type="monotone" dataKey="value" stroke="var(--text-secondary)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="rounded-md border border-border-soft bg-surface-primary p-6">
        <h3 className="text-base font-semibold text-text-primary">Operational Impact Summary</h3>
        <p className="mt-4 text-sm leading-6 text-text-secondary">Forecast indicates additional legal analyst capacity for two review cycles and incremental intake latency until automated clause extraction confidence crosses threshold.</p>
      </section>
    </div>
  );
}

function ChartsTab() {
  return (
    <div className="space-y-8">
      <section className="rounded-md border border-border-soft bg-surface-primary p-6">
        <h3 className="text-base font-semibold text-text-primary">Risk Trend</h3>
        <div className="mt-4 h-[300px] w-full" role="img" aria-label="Risk trend line chart">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={riskTrend} margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
              <CartesianGrid stroke="var(--border-soft)" strokeDasharray="2 6" />
              <XAxis dataKey="week" tick={{ fill: "var(--text-muted)", fontSize: 12 }} axisLine={{ stroke: "var(--border-primary)" }} tickLine={false} />
              <YAxis tick={{ fill: "var(--text-muted)", fontSize: 12 }} axisLine={{ stroke: "var(--border-primary)" }} tickLine={false} width={36} />
              <MonoTooltip />
              <Line type="monotone" dataKey="value" stroke="var(--text-primary)" strokeWidth={2.2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="rounded-md border border-border-soft bg-surface-primary p-6">
        <h3 className="text-base font-semibold text-text-primary">Impact Distribution</h3>
        <div className="mt-4 h-[300px] w-full" role="img" aria-label="Impact distribution bar chart">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={impactDistribution} margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
              <CartesianGrid stroke="var(--border-soft)" strokeDasharray="2 6" vertical={false} />
              <XAxis dataKey="group" tick={{ fill: "var(--text-muted)", fontSize: 12 }} axisLine={{ stroke: "var(--border-primary)" }} tickLine={false} />
              <YAxis tick={{ fill: "var(--text-muted)", fontSize: 12 }} axisLine={{ stroke: "var(--border-primary)" }} tickLine={false} width={36} />
              <MonoTooltip
                labelFormatter={(label) => `${label} Severity`}
                formatter={(value) => [`${value}`, "Value"]}
              />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {impactDistribution.map((entry, index) => (
                  <Cell key={entry.group} fill={chartTones[index]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="rounded-md border border-border-soft bg-surface-primary p-6">
        <h3 className="text-base font-semibold text-text-primary">Severity Breakdown</h3>
        <div className="mt-4 h-[300px] w-full" role="img" aria-label="Severity breakdown donut chart">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={severityBreakdown} dataKey="value" nameKey="name" innerRadius={76} outerRadius={112}>
                {severityBreakdown.map((entry, index) => (
                  <Cell key={entry.name} fill={chartTones[index]} />
                ))}
              </Pie>
              <MonoTooltip formatter={(value, name) => [`${value}%`, name]} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}

type ChatMessage = { role: "assistant" | "user"; text: string };

const suggestedQuestions = [
  "What is this regulation about?",
  "Does this affect banking sector?",
  "What compliance actions are required?",
  "What penalties are mentioned?",
];

function AIChatPanel() {
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);

  const sendMessage = async (incomingMessage?: string) => {
    const message = (incomingMessage ?? draft).trim();
    if (!message || isSending) {
      return;
    }
    if (message.length < 3) {
      setMessages((prev) => [...prev, { role: "assistant", text: "Please enter at least 3 characters." }]);
      return;
    }

    setDraft("");
    setMessages((prev) => [...prev, { role: "user", text: message }]);
    setIsSending(true);
    try {
      const response = await apiClient.chatAssistant({ message, organizationProfile: DEFAULT_ORG_PROFILE });
      setMessages((prev) => [...prev, { role: "assistant", text: response.reply }]);
    } catch (error) {
      const fallback = error instanceof ApiError ? `Assistant unavailable: ${error.message}` : "Assistant unavailable right now.";
      setMessages((prev) => [...prev, { role: "assistant", text: fallback }]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <section className="flex min-h-[600px] flex-col rounded-md border border-border-primary bg-surface-card p-8">
      <header className="border-b border-border-soft pb-4">
        <h3 className="text-lg font-semibold text-text-primary">AI Assistant</h3>
        <p className="mt-2 text-sm text-text-secondary">Focused interpretation workspace for this document context.</p>
      </header>

      <div className="mt-4 flex flex-wrap gap-2">
        {suggestedQuestions.map((question) => (
          <button
            key={question}
            type="button"
            onClick={() => void sendMessage(question)}
            disabled={isSending}
            className="rounded-md border border-border-soft bg-surface-primary px-3 py-1.5 text-xs text-text-secondary hover:bg-surface-elevated disabled:opacity-50"
          >
            {question}
          </button>
        ))}
      </div>

      <div className="mt-6 flex-1 space-y-4 overflow-y-auto pr-1">
        {messages.length === 0 ? <p className="text-sm text-text-muted">Select a suggested question or type your own.</p> : null}
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={[
              "rounded-md border border-border-soft px-4 py-3 text-sm leading-6",
              message.role === "user" ? "bg-surface-elevated text-text-primary" : "bg-surface-primary text-text-secondary",
            ].join(" ")}
          >
            {message.text}
          </div>
        ))}
      </div>

      <div className="mt-6 flex items-center gap-3 border-t border-border-soft pt-4">
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              void sendMessage();
            }
          }}
          placeholder="Ask for interpretation or impact analysis"
          className="h-11 w-full rounded-md border border-border-soft bg-bg-secondary px-4 text-sm text-text-primary placeholder:text-text-muted focus:border-border-primary focus:outline-none"
        />
        <button type="button" onClick={() => void sendMessage()} disabled={isSending} className="h-11 rounded-md border border-border-primary bg-surface-elevated px-4 text-sm text-text-primary hover:opacity-90 disabled:opacity-50">
          Send
        </button>
      </div>
    </section>
  );
}

export function DocumentViewerPage() {
  const { documentId } = useParams();
  const [isChatOpenMobile, setIsChatOpenMobile] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisRunResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const runAnalysis = async () => {
      try {
        const response = await apiClient.runAnalysis({ organizationProfile: DEFAULT_ORG_PROFILE, gazetteId: documentId });
        if (active) {
          setAnalysisResult(response);
          setAnalysisError(null);
        }
      } catch (error) {
        if (active) {
          const message = error instanceof ApiError ? `Analysis unavailable: ${error.message}` : "Analysis unavailable right now.";
          setAnalysisError(message);
          setAnalysisResult(null);
        }
      }
    };

    void runAnalysis();
    return () => {
      active = false;
    };
  }, [documentId]);

  return (
    <div className="mx-auto w-full max-w-[1280px] px-8 pb-20 pt-12">
      <motion.section initial="hidden" animate="show" variants={fadeUp} transition={{ duration: 0.22 }} className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-[0.1em] text-text-muted">Analysis Workspace</p>
        <h2 className="mt-4 text-[40px] font-semibold tracking-tight text-text-primary md:text-5xl">Regulatory Document Intelligence</h2>
        <p className="mt-4 max-w-4xl text-base leading-8 text-text-secondary">AI-powered legal interpretation, impact modeling, and strategic breakdown.</p>
        <p className="mt-3 text-sm text-text-muted">Document ID: {documentId}</p>
      </motion.section>

      <motion.section initial="hidden" animate="show" variants={fadeUp} transition={{ duration: 0.24 }} className="mt-8 grid grid-cols-12 gap-8">
        <section className="col-span-12 min-h-[600px] rounded-md border border-border-primary bg-surface-card p-8 lg:col-span-8">
          <Tabs.Root defaultValue="analysis" className="h-full">
            <Tabs.List className="grid grid-cols-3 gap-2 border-b border-border-soft pb-4 md:flex md:items-center md:gap-6" aria-label="Document intelligence tabs">
              <Tabs.Trigger value="analysis" className="rounded-md py-2 text-sm text-text-muted data-[state=active]:font-medium data-[state=active]:text-text-primary md:py-0">
                Analysis
              </Tabs.Trigger>
              <Tabs.Trigger value="impact" className="rounded-md py-2 text-sm text-text-muted data-[state=active]:font-medium data-[state=active]:text-text-primary md:py-0">
                Impact
              </Tabs.Trigger>
              <Tabs.Trigger value="charts" className="rounded-md py-2 text-sm text-text-muted data-[state=active]:font-medium data-[state=active]:text-text-primary md:py-0">
                Charts
              </Tabs.Trigger>
            </Tabs.List>

            <div className="mt-6">
              <Tabs.Content value="analysis">
                <AnalysisTab analysisResult={analysisResult} analysisError={analysisError} />
              </Tabs.Content>
              <Tabs.Content value="impact">
                <ImpactTab analysisResult={analysisResult} />
              </Tabs.Content>
              <Tabs.Content value="charts">
                <ChartsTab />
              </Tabs.Content>
            </div>
          </Tabs.Root>
        </section>

        <section className="col-span-12 lg:hidden">
          <Collapsible.Root open={isChatOpenMobile} onOpenChange={setIsChatOpenMobile}>
            <Collapsible.Trigger className="w-full rounded-md border border-border-primary bg-surface-card px-4 py-3 text-left text-sm font-medium text-text-primary">
              AI Assistant
            </Collapsible.Trigger>
            <Collapsible.Content className="mt-3">
              <AIChatPanel />
            </Collapsible.Content>
          </Collapsible.Root>
        </section>

        <section className="hidden lg:col-span-4 lg:block">
          <AIChatPanel />
        </section>
      </motion.section>
    </div>
  );
}
