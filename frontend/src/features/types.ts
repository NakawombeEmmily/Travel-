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
}
