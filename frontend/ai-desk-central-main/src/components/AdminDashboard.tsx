import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { 
  Ticket, 
  AlertTriangle, 
  Clock, 
  CheckCircle, 
  Users, 
  TrendingUp,
  Filter,
  Search,
  Eye,
  MessageSquare
} from 'lucide-react';
import { Input } from '@/components/ui/input';

// Mock data for demonstration
const mockTickets = [
  {
    id: 'TK-001',
    subject: 'Email not syncing on mobile device',
    priority: 'high',
    status: 'open',
    category: 'email',
    assignee: 'John Smith',
    created: '2 hours ago',
    language: 'English'
  },
  {
    id: 'TK-002', 
    subject: 'प्रिंटर काम नहीं कर रहा',
    priority: 'medium',
    status: 'in-progress',
    category: 'hardware',
    assignee: 'Sarah Johnson',
    created: '4 hours ago',
    language: 'Hindi'
  },
  {
    id: 'TK-003',
    subject: 'VPN connection keeps dropping',
    priority: 'critical',
    status: 'open',
    category: 'network',
    assignee: 'Mike Davis',
    created: '1 hour ago',
    language: 'English'
  },
  {
    id: 'TK-004',
    subject: 'Software license expired',
    priority: 'low',
    status: 'resolved',
    category: 'software',
    assignee: 'Lisa Wong',
    created: '1 day ago',
    language: 'English'
  }
];

const priorityData = [
  { name: 'Critical', value: 15, color: '#ef4444' },
  { name: 'High', value: 35, color: '#f97316' },
  { name: 'Medium', value: 40, color: '#eab308' },
  { name: 'Low', value: 10, color: '#22c55e' }
];

const categoryData = [
  { name: 'Hardware', tickets: 12, resolved: 8 },
  { name: 'Software', tickets: 18, resolved: 15 },
  { name: 'Network', tickets: 8, resolved: 5 },
  { name: 'Email', tickets: 6, resolved: 4 },
  { name: 'Security', tickets: 4, resolved: 3 }
];

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case 'critical': return 'destructive';
    case 'high': return 'warning';
    case 'medium': return 'default';
    case 'low': return 'success';
    default: return 'secondary';
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'open': return 'warning';
    case 'in-progress': return 'default';
    case 'resolved': return 'success';
    default: return 'secondary';
  }
};

export const AdminDashboard = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTicket, setSelectedTicket] = useState<string | null>(null);

  const filteredTickets = mockTickets.filter(ticket =>
    ticket.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
    ticket.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gradient-subtle">
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">IT Admin Dashboard</h1>
            <p className="text-muted-foreground">Manage and monitor all support tickets</p>
          </div>
          <Button variant="professional" size="lg">
            <Filter className="w-4 h-4" />
            Advanced Filters
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="shadow-soft bg-gradient-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Tickets</CardTitle>
              <Ticket className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-primary">48</div>
              <p className="text-xs text-success flex items-center">
                <TrendingUp className="w-3 h-3 mr-1" />
                +12% from last month
              </p>
            </CardContent>
          </Card>

          <Card className="shadow-soft bg-gradient-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Open Tickets</CardTitle>
              <AlertTriangle className="h-4 w-4 text-warning" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-warning">18</div>
              <p className="text-xs text-muted-foreground">Awaiting response</p>
            </CardContent>
          </Card>

          <Card className="shadow-soft bg-gradient-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-primary">2.4h</div>
              <p className="text-xs text-success flex items-center">
                <TrendingUp className="w-3 h-3 mr-1" />
                -15% improvement
              </p>
            </CardContent>
          </Card>

          <Card className="shadow-soft bg-gradient-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Resolution Rate</CardTitle>
              <CheckCircle className="h-4 w-4 text-success" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-success">94.2%</div>
              <p className="text-xs text-success flex items-center">
                <TrendingUp className="w-3 h-3 mr-1" />
                Excellent performance
              </p>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="tickets" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="tickets">Active Tickets</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="team">Team Performance</TabsTrigger>
          </TabsList>

          <TabsContent value="tickets" className="space-y-6">
            <Card className="shadow-medium bg-gradient-card">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Ticket Management</CardTitle>
                    <CardDescription>Monitor and manage all support requests</CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Search tickets..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10 w-64"
                      />
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {filteredTickets.map((ticket) => (
                    <div
                      key={ticket.id}
                      className="p-4 rounded-lg border bg-background/50 hover:bg-accent/50 transition-all duration-300 cursor-pointer shadow-soft hover:shadow-medium"
                      onClick={() => setSelectedTicket(ticket.id === selectedTicket ? null : ticket.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div>
                            <p className="font-medium text-foreground">{ticket.id}</p>
                            <p className="text-sm text-muted-foreground">{ticket.created}</p>
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-foreground line-clamp-1">{ticket.subject}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge variant={getPriorityColor(ticket.priority) as any} className="text-xs">
                                {ticket.priority.toUpperCase()}
                              </Badge>
                              <Badge variant={getStatusColor(ticket.status) as any} className="text-xs">
                                {ticket.status.replace('-', ' ').toUpperCase()}
                              </Badge>
                              <span className="text-xs text-muted-foreground">{ticket.language}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-muted-foreground">{ticket.assignee}</span>
                          <Button variant="ghost" size="sm">
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <MessageSquare className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                      
                      {selectedTicket === ticket.id && (
                        <div className="mt-4 p-4 bg-muted/50 rounded-lg">
                          <p className="text-sm text-muted-foreground mb-2">AI Analysis:</p>
                          <p className="text-sm">
                            Category: <strong>{ticket.category}</strong> | 
                            Language detected: <strong>{ticket.language}</strong> | 
                            Suggested action: Contact user within 2 hours
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="shadow-medium bg-gradient-card">
                <CardHeader>
                  <CardTitle>Priority Distribution</CardTitle>
                  <CardDescription>Breakdown of ticket priorities</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={priorityData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={120}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {priorityData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card className="shadow-medium bg-gradient-card">
                <CardHeader>
                  <CardTitle>Category Performance</CardTitle>
                  <CardDescription>Tickets by category and resolution rate</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={categoryData}>
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="tickets" fill="hsl(var(--primary))" name="Total Tickets" />
                      <Bar dataKey="resolved" fill="hsl(var(--success))" name="Resolved" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="team" className="space-y-6">
            <Card className="shadow-medium bg-gradient-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Team Performance Overview
                </CardTitle>
                <CardDescription>Individual and team metrics</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <Users className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                  <p className="text-lg font-medium text-foreground mb-2">Team Analytics Coming Soon</p>
                  <p className="text-muted-foreground">
                    Individual performance metrics, workload distribution, and team efficiency reports will be available here.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};