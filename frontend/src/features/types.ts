export type TripStatus =
  | "inquiry"
  | "confirmed"
  | "in_progress"
  | "completed"
  | "cancelled";

export type TripPurpose =
  | "tourism"
  | "business"
  | "study"
  | "medical"
  | "other";

export interface Trip {
  id: string;
  client_id: string;
  client_name?: string | null;
  destination_country: string;
  travel_start_date: string;
  travel_end_date?: string | null;
  purpose: TripPurpose;
  itinerary_notes?: string | null;
  total_cost: string;
  currency: string;
  status: TripStatus;
  created_at: string;
  updated_at: string;
}

export interface TripListResponse {
  items: Trip[];
  total: number;
  page: number;
  page_size: number;
}

export type VisaStatus =
  | "not_required"
  | "not_started"
  | "documents_pending"
  | "submitted"
  | "in_review"
  | "approved"
  | "rejected"
  | "expired";

export interface Visa {
  id: string;
  client_id: string;
  client_name?: string | null;
  trip_id?: string | null;
  destination_country: string;
  visa_type?: string | null;
  application_date?: string | null;
  submission_date?: string | null;
  reference_number?: string | null;
  status: VisaStatus;
  approval_date?: string | null;
  expiry_date?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface VisaHistory {
  id: string;
  old_status?: string | null;
  new_status: string;
  changed_by?: string | null;
  changed_at: string;
  note?: string | null;
}

export interface VisaDetail extends Visa {
  history: VisaHistory[];
}

export interface VisaListResponse {
  items: Visa[];
  total: number;
  page: number;
  page_size: number;
}

export interface DocumentItem {
  id: string;
  client_id?: string | null;
  visa_id?: string | null;
  original_filename: string;
  file_type?: string | null;
  file_size?: number | null;
  is_encrypted: boolean;
  checksum?: string | null;
  uploaded_at: string;
}

export interface DocumentListResponse {
  items: DocumentItem[];
  total: number;
}

export interface UpcomingDeparture {
  trip_id: string;
  client_name?: string | null;
  destination_country: string;
  travel_start_date: string;
  status: string;
}

export interface DashboardSummary {
  active_clients: number;
  trips_in_progress: number;
  pending_visas: number;
  revenue_mtd: string;
  passports_expiring_soon: number;
  visas_expiring_soon: number;
  trips_by_status: Record<string, number>;
  visas_by_status: Record<string, number>;
  upcoming_departures: UpcomingDeparture[];
  feedback_count: number;
  feedback_average: number;
  feedback_by_sentiment: Record<string, number>;
  open_leads: number;
  leads_by_status: Record<string, number>;
  open_tasks: number;
  overdue_tasks: number;
}

export type Sentiment = "positive" | "neutral" | "negative" | "mixed";

export type FeedbackCategory =
  | "service"
  | "price"
  | "visa_support"
  | "communication";

export interface Feedback {
  id: string;
  client_id: string;
  client_name?: string | null;
  trip_id?: string | null;
  rating: number;
  comment?: string | null;
  category?: string | null;
  sentiment: string;
  feedback_date: string;
  created_at: string;
}

export interface FeedbackListResponse {
  items: Feedback[];
  total: number;
  page: number;
  page_size: number;
}

export interface FeedbackStats {
  count: number;
  average_rating: number;
  by_sentiment: Record<string, number>;
  by_category: Record<string, number>;
}

export type InteractionType =
  | "call"
  | "email"
  | "whatsapp"
  | "meeting"
  | "other";

export interface Interaction {
  id: string;
  client_id: string;
  client_name?: string | null;
  interaction_type: string;
  notes?: string | null;
  follow_up_date?: string | null;
  contacted_by?: string | null;
  created_at: string;
}

export interface InteractionListResponse {
  items: Interaction[];
  total: number;
  page: number;
  page_size: number;
}

export type LeadStatus =
  | "lead"
  | "contacted"
  | "quote_sent"
  | "negotiation"
  | "won"
  | "lost";

export interface Lead {
  id: string;
  client_id?: string | null;
  full_name: string;
  email?: string | null;
  phone?: string | null;
  source?: string | null;
  status: string;
  assigned_to?: string | null;
  created_at: string;
  updated_at: string;
}

export interface LeadListResponse {
  items: Lead[];
  total: number;
  page: number;
  page_size: number;
}

export interface Tag {
  id: string;
  name: string;
  color: string;
}

export interface TagListResponse {
  items: Tag[];
}

export type TaskStatus = "pending" | "in_progress" | "completed" | "cancelled";

export type TaskPriority = "low" | "medium" | "high";

export interface Task {
  id: string;
  client_id: string;
  client_name?: string | null;
  title: string;
  description?: string | null;
  assigned_to?: string | null;
  due_date?: string | null;
  status: string;
  priority: string;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskListResponse {
  items: Task[];
  total: number;
  page: number;
  page_size: number;
}

export interface TaskStats {
  open: number;
  overdue: number;
  due_soon: number;
}

export type PaymentStatus =
  | "pending"
  | "completed"
  | "failed"
  | "refunded"
  | "partial";

export type PaymentMethod =
  | "card"
  | "mobile_money"
  | "bank_transfer"
  | "cash";

export interface PaymentInstallment {
  id: string;
  payment_id: string;
  amount: string;
  due_date?: string | null;
  paid_at?: string | null;
  status: string;
  created_at: string;
}

export interface Payment {
  id: string;
  client_id: string;
  client_name?: string | null;
  trip_id?: string | null;
  amount: string;
  currency: string;
  exchange_rate: string;
  method: string;
  provider: string;
  provider_transaction_id?: string | null;
  status: string;
  paid_at?: string | null;
  invoice_number?: string | null;
  notes?: string | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
  installments: PaymentInstallment[];
}

export interface PaymentListResponse {
  items: Payment[];
  total: number;
  page: number;
  page_size: number;
}

export interface PaymentStats {
  count: number;
  by_status: Record<string, number>;
  total_collected: string;
  outstanding: string;
}

export interface OutboxEvent {
  id: string;
  event_id: string;
  aggregate_type: string;
  aggregate_id: string;
  event_type: string;
  status: string;
  attempts: number;
  max_attempts: number;
  last_attempt_at?: string | null;
  next_attempt_at?: string | null;
  error_message?: string | null;
  created_at: string;
  processed_at?: string | null;
}

export interface OutboxListResponse {
  items: OutboxEvent[];
  total: number;
  page: number;
  page_size: number;
}

export interface OutboxProcessResult {
  processed: number;
  completed: number;
  failed: number;
  pending: number;
}

export interface ReconcileResult {
  checked: number;
  created: number;
  updated: number;
  mismatched: number;
  errors: string[];
}

export interface RevenueSummary {
  id: string;
  summary_date: string;
  period_type: string;
  total_amount: string;
  currency: string;
  transaction_count: number;
  completed_count: number;
  failed_count: number;
  refunded_count: number;
  created_at: string;
}
