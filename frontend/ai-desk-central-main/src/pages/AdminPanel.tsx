import React from 'react';
import { AdminDashboard } from '@/components/AdminDashboard';
import { TicketList } from '@/components/TicketList';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, LayoutDashboard, ListCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

const AdminPanel = () => {
  return (
    <div className="min-h-screen bg-gradient-subtle">
      <div className="container mx-auto p-4">
        <div className="mb-6">
          <Link to="/">
            <Button variant="ghost" className="flex items-center gap-2">
              <ArrowLeft className="w-4 h-4" />
              Back to Landing Page
            </Button>
          </Link>
        </div>
        
        <Tabs defaultValue="dashboard" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 max-w-md">
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <LayoutDashboard className="h-4 w-4" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="tickets" className="flex items-center gap-2">
              <ListCheck className="h-4 w-4" />
              All Tickets
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="dashboard" className="space-y-6">
            <AdminDashboard />
          </TabsContent>
          
          <TabsContent value="tickets" className="space-y-6">
            <TicketList showFilters={true} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default AdminPanel;