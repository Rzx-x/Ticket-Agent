import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Search,
  Filter,
  SortAsc,
  SortDesc,
  Clock,
  User,
  Mail,
  Tag,
  AlertCircle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { useTickets, useOfflineSync } from '@/hooks/useTickets';
import { TicketResponse } from '@/services/api';
import { cn } from '@/lib/utils';
import { format, formatDistanceToNow } from 'date-fns';

interface TicketListProps {
  showFilters?: boolean;
  maxTickets?: number;
  className?: string;
}

const priorityColors = {
  low: 'bg-green-100 text-green-800 border-green-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  critical: 'bg-red-100 text-red-800 border-red-200',
};

const statusColors = {
  open: 'bg-blue-100 text-blue-800 border-blue-200',
  in_progress: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  resolved: 'bg-green-100 text-green-800 border-green-200',
  closed: 'bg-gray-100 text-gray-800 border-gray-200',
};

const statusIcons = {
  open: AlertCircle,
  in_progress: RefreshCw,
  resolved: CheckCircle,
  closed: XCircle,
};

export const TicketList: React.FC<TicketListProps> = ({ 
  showFilters = true, 
  maxTickets,
  className 
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [sortBy, setSortBy] = useState<'created_at' | 'updated_at' | 'priority'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState(1);
  
  const { isOnline } = useOfflineSync();

  // Prepare filters for API call
  const filters = useMemo(() => ({
    page,
    per_page: maxTickets || 20,
    search: searchTerm || undefined,
    status: statusFilter || undefined,
    priority: priorityFilter || undefined,
    category: categoryFilter || undefined,
  }), [page, maxTickets, searchTerm, statusFilter, priorityFilter, categoryFilter]);

  const { 
    tickets, 
    pagination, 
    isLoading, 
    error, 
    refetch,
    isRefetching 
  } = useTickets(filters);

  // Sort tickets locally for better responsiveness
  const sortedTickets = useMemo(() => {
    if (!tickets) return [];
    
    const sorted = [...tickets].sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'updated_at':
          comparison = new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
          break;
        case 'priority':
          const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
          comparison = (priorityOrder[a.priority as keyof typeof priorityOrder] || 0) - 
                     (priorityOrder[b.priority as keyof typeof priorityOrder] || 0);
          break;
        default:
          comparison = 0;
      }
      
      return sortOrder === 'desc' ? -comparison : comparison;
    });

    return maxTickets ? sorted.slice(0, maxTickets) : sorted;
  }, [tickets, sortBy, sortOrder, maxTickets]);

  const handleRefresh = () => {
    refetch();
  };

  const handleSortToggle = (field: typeof sortBy) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const TicketCard: React.FC<{ ticket: TicketResponse }> = ({ ticket }) => {
    const StatusIcon = statusIcons[ticket.status as keyof typeof statusIcons] || AlertCircle;
    
    return (
      <Card className="hover:shadow-md transition-all duration-300 border-l-4 border-l-blue-500">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <CardTitle className="text-lg font-semibold text-foreground truncate">
                {ticket.title}
              </CardTitle>
              <CardDescription className="text-sm text-muted-foreground mt-1">
                ID: {ticket.id}
              </CardDescription>
            </div>
            <div className="flex flex-col gap-2 items-end">
              <Badge 
                variant="outline" 
                className={cn(statusColors[ticket.status as keyof typeof statusColors], "flex items-center gap-1")}
              >
                <StatusIcon className="h-3 w-3" />
                {ticket.status.replace('_', ' ').toUpperCase()}
              </Badge>
              <Badge 
                variant="outline"
                className={priorityColors[ticket.priority as keyof typeof priorityColors]}
              >
                {ticket.priority.toUpperCase()}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground line-clamp-2">
              {ticket.description}
            </p>
            
            <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <User className="h-3 w-3" />
                {ticket.reporter_name}
              </div>
              <div className="flex items-center gap-1">
                <Mail className="h-3 w-3" />
                {ticket.reporter_email}
              </div>
              <div className="flex items-center gap-1">
                <Tag className="h-3 w-3" />
                {ticket.category}
              </div>
              {ticket.department && (
                <div className="flex items-center gap-1">
                  <Tag className="h-3 w-3" />
                  {ticket.department}
                </div>
              )}
            </div>

            {ticket.ai_suggestions && ticket.ai_suggestions.length > 0 && (
              <div className="mt-3 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-md">
                <p className="text-xs text-blue-700 dark:text-blue-300 font-medium mb-1">
                  AI Suggestions:
                </p>
                <ul className="text-xs text-blue-600 dark:text-blue-400 list-disc list-inside">
                  {ticket.ai_suggestions.slice(0, 2).map((suggestion, index) => (
                    <li key={index} className="truncate">{suggestion}</li>
                  ))}
                </ul>
              </div>
            )}
            
            <div className="flex items-center justify-between pt-2 border-t">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                Created {formatDistanceToNow(new Date(ticket.created_at), { addSuffix: true })}
              </div>
              {ticket.updated_at !== ticket.created_at && (
                <div className="text-xs text-muted-foreground">
                  Updated {formatDistanceToNow(new Date(ticket.updated_at), { addSuffix: true })}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const LoadingSkeleton = () => (
    <div className="space-y-4">
      {Array.from({ length: 3 }).map((_, i) => (
        <Card key={i}>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div className="space-y-2 flex-1">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-3 w-1/4" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-6 w-20" />
                <Skeleton className="h-6 w-16" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-2/3" />
              <div className="flex gap-4">
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-3 w-12" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header with connection status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold">Support Tickets</h2>
          <div className="flex items-center gap-1">
            {isOnline ? (
              <div className="flex items-center gap-1 text-green-600">
                <Wifi className="h-4 w-4" />
                <span className="text-sm">Online</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-red-600">
                <WifiOff className="h-4 w-4" />
                <span className="text-sm">Offline</span>
              </div>
            )}
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={isRefetching}
          className="gap-2"
        >
          <RefreshCw className={cn("h-4 w-4", isRefetching && "animate-spin")} />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      {showFilters && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Filters & Search
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Search</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search tickets..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">Status</label>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="All statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All statuses</SelectItem>
                    <SelectItem value="open">Open</SelectItem>
                    <SelectItem value="in_progress">In Progress</SelectItem>
                    <SelectItem value="resolved">Resolved</SelectItem>
                    <SelectItem value="closed">Closed</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Priority</label>
                <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="All priorities" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All priorities</SelectItem>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Category</label>
                <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="All categories" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All categories</SelectItem>
                    <SelectItem value="hardware">Hardware</SelectItem>
                    <SelectItem value="software">Software</SelectItem>
                    <SelectItem value="network">Network</SelectItem>
                    <SelectItem value="email">Email</SelectItem>
                    <SelectItem value="security">Security</SelectItem>
                    <SelectItem value="access">Access</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sort controls */}
      <div className="flex flex-wrap gap-2 items-center">
        <span className="text-sm font-medium">Sort by:</span>
        <Button
          variant={sortBy === 'created_at' ? 'default' : 'outline'}
          size="sm"
          onClick={() => handleSortToggle('created_at')}
          className="gap-1"
        >
          Created
          {sortBy === 'created_at' && (
            sortOrder === 'desc' ? <SortDesc className="h-3 w-3" /> : <SortAsc className="h-3 w-3" />
          )}
        </Button>
        <Button
          variant={sortBy === 'updated_at' ? 'default' : 'outline'}
          size="sm"
          onClick={() => handleSortToggle('updated_at')}
          className="gap-1"
        >
          Updated
          {sortBy === 'updated_at' && (
            sortOrder === 'desc' ? <SortDesc className="h-3 w-3" /> : <SortAsc className="h-3 w-3" />
          )}
        </Button>
        <Button
          variant={sortBy === 'priority' ? 'default' : 'outline'}
          size="sm"
          onClick={() => handleSortToggle('priority')}
          className="gap-1"
        >
          Priority
          {sortBy === 'priority' && (
            sortOrder === 'desc' ? <SortDesc className="h-3 w-3" /> : <SortAsc className="h-3 w-3" />
          )}
        </Button>
      </div>

      {/* Error handling */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load tickets. {!isOnline && 'You are currently offline. '}
            <Button variant="link" onClick={handleRefresh} className="p-0 h-auto">
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Content */}
      {isLoading ? (
        <LoadingSkeleton />
      ) : sortedTickets.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">
              {searchTerm || statusFilter || priorityFilter || categoryFilter
                ? 'No tickets match your filters.'
                : 'No tickets found.'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {sortedTickets.map((ticket) => (
            <TicketCard key={ticket.id} ticket={ticket} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {pagination && pagination.pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={pagination.page <= 1}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {pagination.page} of {pagination.pages} ({pagination.total} total)
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={pagination.page >= pagination.pages}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
};