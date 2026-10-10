import {
  WorkspaceSessionInfo,
  DashboardResponse,
  EventListResponse,
  ActivityEvent,
  AlertListResponse,
  AlertDetail,
  RuleConfig,
  ReanalyzeResponse,
  ImportPreviewResponse,
  ImportCommitResponse,
  ManualSimulateResponse,
} from '../types';

let cachedCsrfToken: string | null = null;

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}

export function getCsrfToken(): string {
  if (cachedCsrfToken) return cachedCsrfToken;
  const cookieVal = getCookie('sentinel_csrf');
  if (cookieVal) {
    cachedCsrfToken = cookieVal;
    return cookieVal;
  }
  return '';
}

export function setCsrfToken(token: string) {
  cachedCsrfToken = token;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});

  // For state-changing methods, attach CSRF header
  const method = (options.method || 'GET').toUpperCase();
  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
    const csrf = getCsrfToken();
    if (csrf) {
      headers.set('X-CSRF-Token', csrf);
    }
  }

  // Set default JSON accept header
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }

  const response = await fetch(`/api/v1${endpoint}`, {
    ...options,
    headers,
    credentials: 'include', // Ensure cookies are sent
  });

  if (!response.ok) {
    let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // Ignore json parse error
    }
    throw new Error(errorMsg);
  }

  return response.json() as Promise<T>;
}

export const api = {
  // Session & Workspace
  async bootstrapSession(): Promise<WorkspaceSessionInfo> {
    const data = await request<WorkspaceSessionInfo>('/session/bootstrap', { method: 'POST' });
    if (data.csrf_token) {
      setCsrfToken(data.csrf_token);
    }
    return data;
  },

  async getSessionInfo(): Promise<WorkspaceSessionInfo> {
    const data = await request<WorkspaceSessionInfo>('/session/info');
    if (data.csrf_token) {
      setCsrfToken(data.csrf_token);
    }
    return data;
  },

  async resetSession(): Promise<WorkspaceSessionInfo> {
    const data = await request<WorkspaceSessionInfo>('/session/reset', { method: 'POST' });
    if (data.csrf_token) {
      setCsrfToken(data.csrf_token);
    }
    return data;
  },

  // Dashboard
  async getDashboard(params?: { date_from?: string; date_to?: string }): Promise<DashboardResponse> {
    const q = new URLSearchParams();
    if (params?.date_from) q.set('date_from', params.date_from);
    if (params?.date_to) q.set('date_to', params.date_to);
    const qs = q.toString() ? `?${q.toString()}` : '';
    return request<DashboardResponse>(`/dashboard${qs}`);
  },

  // Events
  async getEvents(params: {
    page?: number;
    page_size?: number;
    search?: string;
    actor?: string;
    action?: string;
    status?: string;
    date_from?: string;
    date_to?: string;
    sort_by?: string;
    sort_order?: string;
  }): Promise<EventListResponse> {
    const q = new URLSearchParams();
    if (params.page) q.set('page', params.page.toString());
    if (params.page_size) q.set('page_size', params.page_size.toString());
    if (params.search) q.set('search', params.search);
    if (params.actor) q.set('actor', params.actor);
    if (params.action) q.set('action', params.action);
    if (params.status) q.set('status', params.status);
    if (params.date_from) q.set('date_from', params.date_from);
    if (params.date_to) q.set('date_to', params.date_to);
    if (params.sort_by) q.set('sort_by', params.sort_by);
    if (params.sort_order) q.set('sort_order', params.sort_order);
    return request<EventListResponse>(`/events?${q.toString()}`);
  },

  async getEventDetail(id: string): Promise<ActivityEvent> {
    return request<ActivityEvent>(`/events/${id}`);
  },

  // Ingestion
  async previewUpload(file: File): Promise<ImportPreviewResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return request<ImportPreviewResponse>('/ingest/preview', {
      method: 'POST',
      body: formData,
    });
  },

  async commitUpload(file: File): Promise<ImportCommitResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return request<ImportCommitResponse>('/ingest/commit', {
      method: 'POST',
      body: formData,
    });
  },

  async seedSampleData(): Promise<{ message: string; imported_count: number; duplicate_count: number; alerts_created: number }> {
    return request<{ message: string; imported_count: number; duplicate_count: number; alerts_created: number }>('/ingest/sample', {
      method: 'POST',
    });
  },

  async simulateEvent(eventData: Record<string, any>): Promise<ManualSimulateResponse> {
    return request<ManualSimulateResponse>('/ingest/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(eventData),
    });
  },

  // Alerts
  async getAlerts(params: {
    page?: number;
    page_size?: number;
    severity?: string;
    rule_code?: string;
    actor?: string;
    review_status?: string;
    is_active?: boolean;
    date_from?: string;
    date_to?: string;
    sort_by?: string;
    sort_order?: string;
  }): Promise<AlertListResponse> {
    const q = new URLSearchParams();
    if (params.page) q.set('page', params.page.toString());
    if (params.page_size) q.set('page_size', params.page_size.toString());
    if (params.severity) q.set('severity', params.severity);
    if (params.rule_code) q.set('rule_code', params.rule_code);
    if (params.actor) q.set('actor', params.actor);
    if (params.review_status) q.set('review_status', params.review_status);
    if (params.is_active !== undefined) q.set('is_active', String(params.is_active));
    if (params.date_from) q.set('date_from', params.date_from);
    if (params.date_to) q.set('date_to', params.date_to);
    if (params.sort_by) q.set('sort_by', params.sort_by);
    if (params.sort_order) q.set('sort_order', params.sort_order);
    return request<AlertListResponse>(`/alerts?${q.toString()}`);
  },

  async getAlertDetail(id: string): Promise<AlertDetail> {
    return request<AlertDetail>(`/alerts/${id}`);
  },

  async updateAlertReview(id: string, payload: { review_status: string; note: string; author?: string }): Promise<AlertDetail> {
    return request<AlertDetail>(`/alerts/${id}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  },

  // Rules
  async getRules(): Promise<RuleConfig[]> {
    return request<RuleConfig[]>('/rules');
  },

  async updateRule(ruleCode: string, payload: { is_enabled: boolean; config: Record<string, any> }): Promise<RuleConfig> {
    return request<RuleConfig>(`/rules/${ruleCode}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  },

  async reanalyze(): Promise<ReanalyzeResponse> {
    return request<ReanalyzeResponse>('/rules/reanalyze', { method: 'POST' });
  },

  // Reports Preview
  async getReportPreview(params?: {
    date_from?: string;
    date_to?: string;
    severity?: string;
    review_status?: string;
    rule_code?: string;
    actor?: string;
  }): Promise<any> {
    const q = new URLSearchParams();
    if (params?.date_from) q.set('date_from', params.date_from);
    if (params?.date_to) q.set('date_to', params.date_to);
    if (params?.severity) q.set('severity', params.severity);
    if (params?.review_status) q.set('review_status', params.review_status);
    if (params?.rule_code) q.set('rule_code', params.rule_code);
    if (params?.actor) q.set('actor', params.actor);
    const qs = q.toString() ? `?${q.toString()}` : '';
    return request<any>(`/reports/preview${qs}`);
  },
};
