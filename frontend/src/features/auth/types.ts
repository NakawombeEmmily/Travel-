export type UserRole =
  | "super_admin"
  | "admin"
  | "agent"
  | "accountant"
  | "read_only";

export interface Client {
  id: string;
  full_name: string;
  date_of_birth?: string | null;
  gender?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  passport_number_masked: string;
  passport_issue_date?: string | null;
  passport_expiry_date?: string | null;
  issuing_country?: string | null;
  nationality?: string | null;
  emergency_contact?: string | null;
  consent_given: boolean;
  passport_expiring_soon: boolean;
  created_at: string;
  updated_at: string;
}

export interface ClientListResponse {
  items: Client[];
  total: number;
  page: number;
  page_size: number;
}
