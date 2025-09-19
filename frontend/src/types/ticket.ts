// TypeScript interfaces for the Ticket Agent system

export enum TicketSource {
  EMAIL = 'email',
  SMS = 'sms',
  GLPI = 'glpi',
  SOLMAN = 'solman',
  WEB = 'web',
  PHONE = 'phone'
}

export enum TicketUrgency {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export enum TicketStatus {
  OPEN = 'open',
  IN_PROGRESS = 'in_progress',
  PENDING = 'pending',
  RESOLVED = 'resolved',
  CLOSED = 'closed'
}

export enum InteractionType {
  USER_MESSAGE = 'user_message',
  AI_RESPONSE = 'ai_response',
  AGENT_RESPONSE = 'agent_response',
  SYSTEM_NOTE = 'system_note',
  EMAIL_SENT = 'email_sent',
  SMS_SENT = 'sms_sent'
}

export interface TicketInteraction {
  id: string;
  ticket_id: string;
  interaction_type: InteractionType | string;
  content: string;
  sender?: string;
  recipient?: string;
  is_internal: boolean;
  created_at: string;
}

export interface TicketAttachment {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  content_type: string;
  uploaded_by?: string;
  created_at: string;
}

export interface Ticket {
  id: string;
  ticket_number?: string;
  external_id?: string;
  source: TicketSource | string;
  user_email?: string;
  user_phone?: string;
  user_name?: string;
  subject?: string;
  text: string; // For compatibility with existing code
  description?: string;
  language: string;
  category?: string;
  subcategory?: string;
  urgency: TicketUrgency | string;
  priority?: number;
  status: TicketStatus | string;
  assigned_to?: string;
  assigned_group?: string;
  ai_processed?: boolean;
  ai_response?: string;
  ai_confidence?: number;
  resolution_notes?: string;
  resolution_time_minutes?: number;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  closed_at?: string;
  tags?: string;
  interactions?: TicketInteraction[];
  attachments?: TicketAttachment[];
}

export interface CreateTicketRequest {
  source: TicketSource;
  user_email: string;
  user_phone?: string;
  user_name?: string;
  subject: string;
  description: string;
  urgency?: TicketUrgency;
  category?: string;
  external_id?: string;
}

export interface UpdateTicketRequest {
  status?: TicketStatus;
  assigned_to?: string;
  assigned_group?: string;
  resolution_notes?: string;
  category?: string;
  urgency?: TicketUrgency;
  tags?: string;
}

export interface DashboardStats {
  total_tickets: number;
  open_tickets: number;
  in_progress_tickets?: number;
  resolved_tickets: number;
  closed_tickets?: number;
  avg_resolution_time: number;
  success_rate: number;
  categories: Record<string, number>;
  urgency_breakdown: Record<string, number>;
  ai_processing_rate?: number;
  recent_activity?: any[];
}

export interface AnalyticsResponse extends DashboardStats {
  average_resolution_time_hours: number;
  tickets_by_category: Record<string, number>;
  tickets_by_urgency: Record<string, number>;
  tickets_by_source: Record<string, number>;
}

export interface SearchRequest {
  query: string;
  limit?: number;
  category_filter?: string;
  status_filter?: TicketStatus;
  urgency_filter?: TicketUrgency;
}

export interface SimilarTicketResponse {
  ticket_id: string;
  ticket_number: string;
  subject: string;
  category?: string;
  similarity_score: number;
  status: string;
  resolution_notes?: string;
}

export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface SubmitTicketResponse {
  id: string;
  ticket_number: string;
  ai_response?: string;
  category?: string;
  urgency?: string;
  status: string;
  created_at: string;
}

// Form interfaces for React components
export interface TicketFormData {
  text: string;
  source: string;
  user_email: string;
  user_name?: string;
  user_phone?: string;
  urgency?: string;
  category?: string;
}

export interface MessageFormData {
  text: string;
  user_email?: string;
  user_name?: string;
}

// Component props interfaces
export interface TicketFormProps {
  onSubmit?: (data: TicketFormData) => Promise<void>;
  initialData?: Partial<TicketFormData>;
  isLoading?: boolean;
}

export interface DashboardProps {
  refreshInterval?: number;
  showRealTimeUpdates?: boolean;
}

// Error interfaces
export interface APIError {
  message: string;
  field?: string;
  details?: Record<string, any>;
}

export interface ValidationError extends APIError {
  field: string;
}

// Hook return types
export interface UseTicketsReturn {
  tickets: Ticket[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  createTicket: (data: CreateTicketRequest) => Promise<Ticket>;
  updateTicket: (id: string, data: UpdateTicketRequest) => Promise<Ticket>;
}

export interface UseAnalyticsReturn {
  stats: DashboardStats | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}