import { useState, useCallback } from 'react';
import type { 
  Ticket, 
  CreateTicketRequest, 
  UpdateTicketRequest, 
  DashboardStats,
  UseTicketsReturn,
  UseAnalyticsReturn,
  APIError
} from '@/types/ticket';

// Hook for managing tickets
export function useTickets(): UseTicketsReturn {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/tickets');
      if (!response.ok) {
        throw new Error(`Failed to fetch tickets: ${response.status}`);
      }
      
      const data = await response.json();
      setTickets(Array.isArray(data) ? data : []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Error fetching tickets:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const createTicket = useCallback(async (data: CreateTicketRequest): Promise<Ticket> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/tickets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `Failed to create ticket: ${response.status}`);
      }
      
      const newTicket = await response.json();
      setTickets(prev => [newTicket, ...prev]);
      return newTicket;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create ticket';
      setError(errorMessage);
      console.error('Error creating ticket:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateTicket = useCallback(async (id: string, data: UpdateTicketRequest): Promise<Ticket> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/tickets/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `Failed to update ticket: ${response.status}`);
      }
      
      const updatedTicket = await response.json();
      setTickets(prev => prev.map(ticket => 
        ticket.id === id ? updatedTicket : ticket
      ));
      return updatedTicket;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update ticket';
      setError(errorMessage);
      console.error('Error updating ticket:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    tickets,
    loading,
    error,
    refresh,
    createTicket,
    updateTicket
  };
}

// Hook for managing analytics data
export function useAnalytics(): UseAnalyticsReturn {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/analytics/dashboard');
      if (!response.ok) {
        throw new Error(`Failed to fetch analytics: ${response.status}`);
      }
      
      const data = await response.json();
      setStats(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Error fetching analytics:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    stats,
    loading,
    error,
    refresh
  };
}

// Hook for API calls with error handling
export function useAPI() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const makeRequest = useCallback(async <T>(
    url: string,
    options?: RequestInit
  ): Promise<T> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });
      
      if (!response.ok) {
        let errorMessage = `HTTP error! status: ${response.status}`;
        
        try {
          const errorData: APIError = await response.json();
          errorMessage = errorData.message || errorMessage;
        } catch {
          // If JSON parsing fails, use the default error message
        }
        
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('API request failed:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    loading,
    error,
    makeRequest,
    clearError
  };
}

// Hook for form validation
export function useFormValidation() {
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateEmail = useCallback((email: string): boolean => {
    const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
    if (!emailRegex.test(email)) {
      setErrors(prev => ({ ...prev, email: 'Please enter a valid email address' }));
      return false;
    }
    setErrors(prev => ({ ...prev, email: '' }));
    return true;
  }, []);

  const validateRequired = useCallback((value: string, field: string): boolean => {
    if (!value.trim()) {
      setErrors(prev => ({ ...prev, [field]: `${field} is required` }));
      return false;
    }
    setErrors(prev => ({ ...prev, [field]: '' }));
    return true;
  }, []);

  const validateLength = useCallback((
    value: string, 
    field: string, 
    min: number, 
    max?: number
  ): boolean => {
    if (value.length < min) {
      setErrors(prev => ({ 
        ...prev, 
        [field]: `${field} must be at least ${min} characters` 
      }));
      return false;
    }
    if (max && value.length > max) {
      setErrors(prev => ({ 
        ...prev, 
        [field]: `${field} must be no more than ${max} characters` 
      }));
      return false;
    }
    setErrors(prev => ({ ...prev, [field]: '' }));
    return true;
  }, []);

  const clearErrors = useCallback(() => {
    setErrors({});
  }, []);

  const hasErrors = Object.values(errors).some(error => error.length > 0);

  return {
    errors,
    validateEmail,
    validateRequired,
    validateLength,
    clearErrors,
    hasErrors
  };
}