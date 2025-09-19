import { toast } from 'sonner';

// Types based on the backend API
export interface ApiResponse<T = any> {
  data?: T;
  detail?: string;
  success: boolean;
  timestamp?: string;
}

export interface TicketCreateRequest {
  title: string;
  description: string;
  reporter_email: string;
  reporter_name: string;
  category: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  department?: string;
  tags?: string[];
}

export interface TicketResponse {
  id: string;
  title: string;
  description: string;
  reporter_email: string;
  reporter_name: string;
  category: string;
  priority: string;
  status: string;
  department: string;
  ai_classification: any;
  ai_suggestions: string[];
  created_at: string;
  updated_at: string;
}

export interface TicketListResponse {
  tickets: TicketResponse[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws';

// Request configuration
const DEFAULT_TIMEOUT = 30000; // 30 seconds
const MAX_RETRIES = 3;
const RETRY_DELAY_BASE = 1000; // 1 second

// Error types
export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'Network error occurred') {
    super(message);
    this.name = 'NetworkError';
  }
}

export class TimeoutError extends Error {
  constructor(message: string = 'Request timed out') {
    super(message);
    this.name = 'TimeoutError';
  }
}

// Utility functions
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const getExponentialBackoffDelay = (attempt: number) => {
  return RETRY_DELAY_BASE * Math.pow(2, attempt) + Math.random() * 1000;
};

const isRetryableError = (error: any): boolean => {
  if (error instanceof NetworkError || error instanceof TimeoutError) {
    return true;
  }
  if (error instanceof APIError) {
    // Retry on server errors (5xx) and rate limiting (429)
    return error.status ? error.status >= 500 || error.status === 429 : false;
  }
  return false;
};

// Token management
class TokenManager {
  private token: string | null = null;
  private refreshPromise: Promise<string> | null = null;

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('auth_token');
    }
    return this.token;
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  async ensureValidToken(): Promise<string | null> {
    const token = this.getToken();
    if (!token) return null;

    // TODO: Add token validation logic
    return token;
  }
}

const tokenManager = new TokenManager();

// HTTP client with retry logic
class HTTPClient {
  private controller: AbortController | null = null;

  async request<T = any>(
    endpoint: string,
    options: RequestInit = {},
    retryAttempt = 0
  ): Promise<ApiResponse<T>> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Setup abort controller for timeout
    this.controller = new AbortController();
    const timeoutId = setTimeout(() => {
      this.controller?.abort();
    }, DEFAULT_TIMEOUT);

    try {
      // Prepare headers
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...options.headers,
      };

      // Add auth token if available
      const token = await tokenManager.ensureValidToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(url, {
        ...options,
        headers,
        signal: this.controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorData: any = {};
        try {
          errorData = await response.json();
        } catch {
          // Response might not be JSON
        }

        if (response.status === 401) {
          tokenManager.clearToken();
          // Redirect to login or show auth error
          toast.error('Authentication required. Please login again.');
          throw new APIError('Authentication required', 401, 'AUTH_REQUIRED');
        }

        throw new APIError(
          errorData.detail || errorData.message || `HTTP ${response.status}`,
          response.status,
          errorData.code,
          errorData
        );
      }

      const data = await response.json();
      return {
        data,
        success: true,
        timestamp: new Date().toISOString(),
      };

    } catch (error) {
      clearTimeout(timeoutId);

      if (error.name === 'AbortError') {
        throw new TimeoutError('Request timed out');
      }

      if (!navigator.onLine) {
        throw new NetworkError('No internet connection');
      }

      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new NetworkError('Network connection failed');
      }

      // Retry logic
      if (isRetryableError(error) && retryAttempt < MAX_RETRIES) {
        const delay = getExponentialBackoffDelay(retryAttempt);
        console.warn(`Request failed, retrying in ${delay}ms... (attempt ${retryAttempt + 1}/${MAX_RETRIES})`);
        
        await sleep(delay);
        return this.request<T>(endpoint, options, retryAttempt + 1);
      }

      throw error;
    }
  }

  get<T = any>(endpoint: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
    const searchParams = params ? new URLSearchParams(params).toString() : '';
    const url = searchParams ? `${endpoint}?${searchParams}` : endpoint;
    return this.request<T>(url, { method: 'GET' });
  }

  post<T = any>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  put<T = any>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  delete<T = any>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  patch<T = any>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
}

// WebSocket client for real-time updates
class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<string, Set<Function>> = new Map();

  connect(ticketId?: string) {
    const url = ticketId ? `${WS_BASE_URL}/tickets/${ticketId}` : `${WS_BASE_URL}/tickets`;
    
    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.emit('connect');
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.emit('message', data);
          
          // Emit specific events based on message type
          if (data.type) {
            this.emit(data.type, data);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        this.emit('disconnect');
        
        // Attempt to reconnect if not explicitly closed
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', error);
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;
    
    console.log(`Scheduling WebSocket reconnection in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      if (this.reconnectAttempts <= this.maxReconnectAttempts) {
        this.connect();
      }
    }, delay);
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket not connected, message not sent:', data);
    }
  }

  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off(event: string, callback?: Function) {
    if (callback) {
      this.listeners.get(event)?.delete(callback);
    } else {
      this.listeners.delete(event);
    }
  }

  private emit(event: string, data?: any) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in WebSocket event callback for '${event}':`, error);
        }
      });
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.listeners.clear();
  }
}

// Main API client
class APIClient {
  private http = new HTTPClient();
  private ws = new WebSocketClient();

  // Auth methods
  async login(username: string, password: string): Promise<AuthResponse> {
    const response = await this.http.post<AuthResponse>('/auth/login', {
      username,
      password,
    });
    
    if (response.data?.access_token) {
      tokenManager.setToken(response.data.access_token);
    }
    
    return response.data!;
  }

  async logout(): Promise<void> {
    try {
      await this.http.post('/auth/logout');
    } finally {
      tokenManager.clearToken();
      this.ws.disconnect();
    }
  }

  // Ticket methods
  async createTicket(ticketData: TicketCreateRequest): Promise<TicketResponse> {
    const response = await this.http.post<TicketResponse>('/tickets', ticketData);
    
    if (response.data) {
      toast.success(`Ticket created successfully! ID: ${response.data.id}`);
    }
    
    return response.data!;
  }

  async getTickets(params?: {
    page?: number;
    per_page?: number;
    status?: string;
    priority?: string;
    category?: string;
    search?: string;
  }): Promise<TicketListResponse> {
    const response = await this.http.get<TicketListResponse>('/tickets', params);
    return response.data!;
  }

  async getTicket(id: string): Promise<TicketResponse> {
    const response = await this.http.get<TicketResponse>(`/tickets/${id}`);
    return response.data!;
  }

  async updateTicket(id: string, data: Partial<TicketResponse>): Promise<TicketResponse> {
    const response = await this.http.patch<TicketResponse>(`/tickets/${id}`, data);
    return response.data!;
  }

  async deleteTicket(id: string): Promise<void> {
    await this.http.delete(`/tickets/${id}`);
    toast.success('Ticket deleted successfully');
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await this.http.get<{ status: string; timestamp: string }>('/health');
    return response.data!;
  }

  // WebSocket methods
  connectWebSocket(ticketId?: string) {
    this.ws.connect(ticketId);
  }

  onTicketUpdate(callback: (ticket: TicketResponse) => void) {
    this.ws.on('ticket_update', callback);
  }

  onTicketCreated(callback: (ticket: TicketResponse) => void) {
    this.ws.on('ticket_created', callback);
  }

  onTicketStatusChange(callback: (data: { id: string; status: string }) => void) {
    this.ws.on('status_change', callback);
  }

  disconnectWebSocket() {
    this.ws.disconnect();
  }
}

// Export singleton instance
export const apiClient = new APIClient();

// Export utility functions for error handling
export const handleApiError = (error: any) => {
  console.error('API Error:', error);

  if (error instanceof NetworkError) {
    toast.error('Network connection failed. Please check your internet connection.');
  } else if (error instanceof TimeoutError) {
    toast.error('Request timed out. Please try again.');
  } else if (error instanceof APIError) {
    if (error.status === 429) {
      toast.error('Too many requests. Please wait a moment and try again.');
    } else if (error.status === 500) {
      toast.error('Server error occurred. Please try again later.');
    } else {
      toast.error(error.message || 'An error occurred while processing your request.');
    }
  } else {
    toast.error('An unexpected error occurred. Please try again.');
  }
};

export const withApiErrorHandling = async <T>(
  apiCall: () => Promise<T>,
  customErrorHandler?: (error: any) => void
): Promise<T | null> => {
  try {
    return await apiCall();
  } catch (error) {
    if (customErrorHandler) {
      customErrorHandler(error);
    } else {
      handleApiError(error);
    }
    return null;
  }
};