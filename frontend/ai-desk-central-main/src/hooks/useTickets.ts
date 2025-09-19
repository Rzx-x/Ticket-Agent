import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { 
  apiClient, 
  TicketResponse, 
  TicketCreateRequest, 
  TicketListResponse,
  handleApiError 
} from '@/services/api';

// Query keys for React Query
export const ticketKeys = {
  all: ['tickets'] as const,
  lists: () => [...ticketKeys.all, 'list'] as const,
  list: (params?: any) => [...ticketKeys.lists(), params] as const,
  details: () => [...ticketKeys.all, 'detail'] as const,
  detail: (id: string) => [...ticketKeys.details(), id] as const,
};

// Hook for fetching ticket list with filters
export const useTickets = (params?: {
  page?: number;
  per_page?: number;
  status?: string;
  priority?: string;
  category?: string;
  search?: string;
}) => {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ticketKeys.list(params),
    queryFn: async (): Promise<TicketListResponse> => {
      try {
        return await apiClient.getTickets(params);
      } catch (error) {
        handleApiError(error);
        throw error;
      }
    },
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    retry: (failureCount, error) => {
      // Don't retry on auth errors
      if (error && typeof error === 'object' && 'status' in error && error.status === 401) {
        return false;
      }
      return failureCount < 3;
    },
  });

  // WebSocket integration for real-time updates
  const wsRef = useRef<boolean>(false);
  
  useEffect(() => {
    if (!wsRef.current) {
      // Connect to WebSocket for ticket updates
      apiClient.connectWebSocket();
      wsRef.current = true;

      // Listen for ticket updates
      apiClient.onTicketCreated((ticket: TicketResponse) => {
        // Update the query cache
        queryClient.setQueryData(ticketKeys.detail(ticket.id), ticket);
        
        // Invalidate list queries to show new ticket
        queryClient.invalidateQueries({ queryKey: ticketKeys.lists() });
        
        toast.success(`New ticket created: ${ticket.title}`, {
          description: `Priority: ${ticket.priority} | Category: ${ticket.category}`,
        });
      });

      apiClient.onTicketUpdate((ticket: TicketResponse) => {
        // Update the specific ticket in cache
        queryClient.setQueryData(ticketKeys.detail(ticket.id), ticket);
        
        // Update the ticket in list queries
        queryClient.setQueriesData(
          { queryKey: ticketKeys.lists() },
          (oldData: TicketListResponse | undefined) => {
            if (!oldData) return oldData;
            
            return {
              ...oldData,
              tickets: oldData.tickets.map(t => 
                t.id === ticket.id ? ticket : t
              ),
            };
          }
        );
        
        toast.info(`Ticket updated: ${ticket.title}`, {
          description: `Status: ${ticket.status}`,
        });
      });

      // Cleanup function
      return () => {
        apiClient.disconnectWebSocket();
        wsRef.current = false;
      };
    }
  }, [queryClient]);

  return {
    ...query,
    tickets: query.data?.tickets || [],
    pagination: query.data ? {
      total: query.data.total,
      page: query.data.page,
      per_page: query.data.per_page,
      pages: query.data.pages,
    } : undefined,
  };
};

// Hook for fetching single ticket
export const useTicket = (id: string) => {
  return useQuery({
    queryKey: ticketKeys.detail(id),
    queryFn: async (): Promise<TicketResponse> => {
      try {
        return await apiClient.getTicket(id);
      } catch (error) {
        handleApiError(error);
        throw error;
      }
    },
    enabled: !!id,
    staleTime: 30 * 1000, // 30 seconds
    retry: (failureCount, error) => {
      // Don't retry on auth errors or 404s
      if (error && typeof error === 'object' && 'status' in error) {
        if (error.status === 401 || error.status === 404) {
          return false;
        }
      }
      return failureCount < 3;
    },
  });
};

// Hook for creating tickets
export const useCreateTicket = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (ticketData: TicketCreateRequest): Promise<TicketResponse> => {
      try {
        return await apiClient.createTicket(ticketData);
      } catch (error) {
        handleApiError(error);
        throw error;
      }
    },
    onSuccess: (data) => {
      // Update query cache with new ticket
      queryClient.setQueryData(ticketKeys.detail(data.id), data);
      
      // Invalidate list queries to include new ticket
      queryClient.invalidateQueries({ queryKey: ticketKeys.lists() });
    },
    onError: (error) => {
      console.error('Failed to create ticket:', error);
    },
  });
};

// Hook for updating tickets
export const useUpdateTicket = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ 
      id, 
      data 
    }: { 
      id: string; 
      data: Partial<TicketResponse> 
    }): Promise<TicketResponse> => {
      try {
        return await apiClient.updateTicket(id, data);
      } catch (error) {
        handleApiError(error);
        throw error;
      }
    },
    onSuccess: (data) => {
      // Update the specific ticket in cache
      queryClient.setQueryData(ticketKeys.detail(data.id), data);
      
      // Update the ticket in list queries
      queryClient.setQueriesData(
        { queryKey: ticketKeys.lists() },
        (oldData: TicketListResponse | undefined) => {
          if (!oldData) return oldData;
          
          return {
            ...oldData,
            tickets: oldData.tickets.map(ticket => 
              ticket.id === data.id ? data : ticket
            ),
          };
        }
      );

      toast.success('Ticket updated successfully');
    },
    onError: (error) => {
      console.error('Failed to update ticket:', error);
    },
  });
};

// Hook for deleting tickets
export const useDeleteTicket = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      try {
        await apiClient.deleteTicket(id);
      } catch (error) {
        handleApiError(error);
        throw error;
      }
    },
    onSuccess: (_, deletedId) => {
      // Remove ticket from cache
      queryClient.removeQueries({ queryKey: ticketKeys.detail(deletedId) });
      
      // Remove from list queries
      queryClient.setQueriesData(
        { queryKey: ticketKeys.lists() },
        (oldData: TicketListResponse | undefined) => {
          if (!oldData) return oldData;
          
          return {
            ...oldData,
            tickets: oldData.tickets.filter(ticket => ticket.id !== deletedId),
            total: oldData.total - 1,
          };
        }
      );
    },
    onError: (error) => {
      console.error('Failed to delete ticket:', error);
    },
  });
};

// Hook for optimistic updates (for better UX)
export const useOptimisticTicketUpdate = () => {
  const queryClient = useQueryClient();

  return {
    updateTicketOptimistically: (id: string, updates: Partial<TicketResponse>) => {
      // Optimistically update the ticket
      queryClient.setQueryData(
        ticketKeys.detail(id),
        (oldData: TicketResponse | undefined) => {
          if (!oldData) return oldData;
          return { ...oldData, ...updates };
        }
      );

      // Also update in list queries
      queryClient.setQueriesData(
        { queryKey: ticketKeys.lists() },
        (oldData: TicketListResponse | undefined) => {
          if (!oldData) return oldData;
          
          return {
            ...oldData,
            tickets: oldData.tickets.map(ticket => 
              ticket.id === id ? { ...ticket, ...updates } : ticket
            ),
          };
        }
      );
    },

    revertOptimisticUpdate: (id: string) => {
      // Invalidate queries to refetch real data
      queryClient.invalidateQueries({ queryKey: ticketKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: ticketKeys.lists() });
    },
  };
};

// Hook for offline support
export const useOfflineSync = () => {
  const queryClient = useQueryClient();

  useEffect(() => {
    const handleOnline = () => {
      toast.success('Connection restored', {
        description: 'Syncing latest data...',
      });
      
      // Refetch all queries when coming back online
      queryClient.invalidateQueries({ queryKey: ticketKeys.all });
    };

    const handleOffline = () => {
      toast.warning('Connection lost', {
        description: 'You are now offline. Changes will be synced when connection is restored.',
      });
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [queryClient]);

  return {
    isOnline: navigator.onLine,
  };
};