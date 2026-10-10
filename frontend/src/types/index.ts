export interface WorkspaceSessionInfo {
  workspace_id: string;
  name: string;
  csrf_token: string;
  expires_at: string;
  is_demo: boolean;
  events_count: number;
  alerts_count: number;
  unreviewed_alerts_count: number;
}

export interface ActivityEvent {
  id: string;
  workspace_id: string;
  batch_id?: string | null;
  fingerprint: string;
  timestamp: string;
  actor: string;
  action: string;
  target: string;
  status: 'success' | 'failed';
  source_ip: string;
  actor_role?: string | null;
  target_role?: string | null;
  previous_role?: string | null;
  command?: string | null;
  approved?: boolean | null;
  approval_reference?: string | null;
  details?: string | null;
  created_at: string;
  alert_ids: string[];
}

export interface EventListResponse {
  items: ActivityEvent[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ReviewHistoryItem {
  id: string;
  alert_id: string;
  previous_status: string;
  new_status: string;
  note: string;
  author: string;
  created_at: string;
}

export interface Alert {
  id: string;
  workspace_id: string;
  rule_code: string;
  rule_version: number;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  trigger_time: string;
  actor: string;
  target: string;
  source_ip: string;
  reason: string;
  evidence_json: string;
  recommended_action: string;
  review_status: 'Open' | 'Investigating' | 'Resolved' | 'False Positive';
  is_active: boolean;
  deactivation_reason?: string | null;
  created_at: string;
  updated_at: string;
  event_ids: string[];
}

export interface AlertDetail extends Alert {
  parsed_evidence?: Record<string, any>;
  correlated_events: ActivityEvent[];
  reviews: ReviewHistoryItem[];
}

export interface AlertListResponse {
  items: Alert[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface RuleConfig {
  id: string;
  workspace_id: string;
  rule_code: string;
  name: string;
  description: string;
  severity: string;
  is_enabled: boolean;
  config: Record<string, any>;
  version: number;
  updated_at: string;
}

export interface ReanalyzeResponse {
  run_id: string;
  events_analyzed: number;
  alerts_created: number;
  alerts_deactivated: number;
  total_active_alerts: number;
  message: string;
}

export interface DashboardMetrics {
  total_events: number;
  total_active_alerts: number;
  critical_alerts: number;
  high_alerts: number;
  medium_alerts: number;
  open_investigations: number;
  distinct_admins: number;
  latest_import_time?: string | null;
  active_rules_count: number;
  total_rules_count: number;
}

export interface SeverityCount {
  severity: string;
  count: number;
  percentage: number;
}

export interface TimelinePoint {
  date: string;
  event_count: number;
  alert_count: number;
}

export interface TopFlaggedActor {
  actor: string;
  total_alerts: number;
  critical_alerts: number;
  high_alerts: number;
  latest_activity: string;
}

export interface ActionDistributionItem {
  action: string;
  count: number;
}

export interface DashboardResponse {
  metrics: DashboardMetrics;
  severity_distribution: SeverityCount[];
  activity_timeline: TimelinePoint[];
  top_flagged_actors: TopFlaggedActor[];
  action_distribution: ActionDistributionItem[];
}

export interface RowValidationError {
  row_number: number;
  field?: string | null;
  message: string;
  raw_data?: Record<string, any>;
}

export interface ImportPreviewResponse {
  filename: string;
  file_format: string;
  total_rows: number;
  valid_rows_count: number;
  error_count: number;
  duplicate_count: number;
  new_rows_count: number;
  errors: RowValidationError[];
  sample_preview: Record<string, any>[];
}

export interface ImportCommitResponse {
  batch_id: string;
  filename: string;
  total_rows: number;
  imported_count: number;
  duplicate_count: number;
  rejected_count: number;
  alerts_generated: number;
  message: string;
}

export interface ManualSimulateResponse {
  event_id: string;
  fingerprint: string;
  is_duplicate: boolean;
  alerts_generated: number;
  message: string;
}
