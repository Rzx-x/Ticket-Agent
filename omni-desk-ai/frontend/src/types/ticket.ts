// src/types/ticket.ts
export interface Ticket {
  id: string;
  source: 'email' | 'glpi' | 'solman' | 'sms';
  text: string;
  language: string;
  category: string;
  urgency: 'Low' | 'Medium' | 'High' | 'Critical';
  ai_response?: string;
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  created_at: string;
  updated_at: string;
  user_email?: string;
  user_name?: string;
}

export interface DashboardStats {
  total_tickets: number;
  open_tickets: number;
  resolved_tickets: number;
  avg_resolution_time: number;
  success_rate: number;
  categories: { [key: string]: number };
  urgency_breakdown: { [key: string]: number };
}