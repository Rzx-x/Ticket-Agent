import React from 'react';
import { AdminDashboard } from '@/components/AdminDashboard';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';
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
        <AdminDashboard />
      </div>
    </div>
  );
};

export default AdminPanel;