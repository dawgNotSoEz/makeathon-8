export type OrganizationProfile = {
  organization_name: string;
  industry: string;
  business_model: string;
  sub_sector?: string;
};

export type AnalysisRunRequest = {
  organizationProfile: OrganizationProfile;
  gazetteId?: string;
};

export type AnalysisRunResponse = {
  relevantPolicies: Array<{ id: string; impactLevel: "High" | "Medium" | "Low" }>;
  impactSummary: string;
  financialImpactProjection: string;
  riskScore: number;
  growthChartData: Array<{ label: string; value: number }>;
};

export type AssistantChatRequest = {
  message: string;
  organizationProfile: OrganizationProfile;
};

export type AssistantChatResponse = {
  reply: string;
  confidence: "LOW" | "MEDIUM" | "HIGH";
  context_used: number;
};

export type DashboardSummaryResponse = {
  totalDocuments: number;
  assignedPolicies: number;
  reviewedPolicies: number;
  pendingPolicies: number;
  documentsByType: Array<{ type: string; count: number }>;
  processingStatus: Array<{ status: string; count: number }>;
};

export type PolicyListItem = {
  id: string;
  title: string;
  authority: string;
  version: string;
  effectiveDate: string;
  status: string;
  assigned: boolean;
};

export type PolicyDetailResponse = PolicyListItem & {
  content: string;
  metadata: Record<string, string | number | boolean | null>;
  sections: Array<{ title: string; content: string; highlight: boolean }>;
};

export type HealthStatus = {
  status: string;
  checks: Record<string, string>;
};

export type GazetteData = unknown;

export type PolicyAnalysis = {
  gazette_id?: string | null;
  subject?: string | null;
  url?: string | null;
  analysis?: {
    policy_name?: string | null;
    ministry?: string | null;
    policy_type?: string | null;
    date_of_issue?: string | null;
    effective_date?: string | null;
    industries_impacted?: string[];
    departments_impacted?: string[];
    compliance_actions_required?: string[];
    penalties?: string | null;
    risk_level?: string | null;
  } | null;
  fallback_text?: string | null;
  error?: string | null;
};

export type PolicyQueryRequest = {
  question: string;
  gazette_id?: string;
};

export type PolicyQueryResponse = {
  answer?: string | null;
  error?: string | null;
  sources?: Array<{
    gazette_id: string;
    subject: string;
    chunk: string;
  }>;
};

export const DEFAULT_ORG_PROFILE: OrganizationProfile = {
  organization_name: "Kira Demo Organization",
  industry: "Finance",
  business_model: "Digital financial services",
  sub_sector: "Payments",
};

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";
const API_AUTH_TOKEN = import.meta.env.VITE_API_AUTH_TOKEN as string | undefined;

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  if (API_AUTH_TOKEN) {
    headers.set("Authorization", `Bearer ${API_AUTH_TOKEN}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const payload = (await response.json()) as { message?: string };
      if (payload.message) {
        message = payload.message;
      }
    } catch {
      // no-op
    }
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

export const apiClient = {
  getHealth: () => request<HealthStatus>("/health", { method: "GET" }),
  getDashboard: () => request<DashboardSummaryResponse>("/api/dashboard", { method: "GET" }),
  getPolicies: () => request<PolicyListItem[]>("/api/policies", { method: "GET" }),
  getGazettes: () => request<GazetteData>("/api/gazettes", { method: "GET" }),
  getPolicyAnalyses: () => request<PolicyAnalysis[]>("/api/policy-analyses", { method: "GET" }),
  getPolicyById: (policyId: string) => request<PolicyDetailResponse>(`/api/policies/${encodeURIComponent(policyId)}`, { method: "GET" }),
  runAnalysis: (body: AnalysisRunRequest) =>
    request<AnalysisRunResponse>("/api/analysis/run", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  chatAssistant: (body: AssistantChatRequest) =>
    request<AssistantChatResponse>("/api/assistant/chat", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  queryPolicy: (body: PolicyQueryRequest) =>
    request<PolicyQueryResponse>("/api/policy-query", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};

export { ApiError };
