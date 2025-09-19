import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { Send, User, Mail, AlertTriangle, CheckCircle2, Wifi, WifiOff } from 'lucide-react';
import { TicketCreateRequest } from '@/services/api';
import { useCreateTicket, useOfflineSync } from '@/hooks/useTickets';

interface TicketFormData {
  name: string;
  email: string;
  category: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  subject: string;
  description: string;
  department?: string;
}

export const TicketForm = () => {
  const { toast } = useToast();
  const createTicketMutation = useCreateTicket();
  const { isOnline } = useOfflineSync();
  
  const [formData, setFormData] = useState<TicketFormData>({
    name: '',
    email: '',
    category: '',
    priority: 'medium' as const,
    subject: '',
    description: ''
  });
  const [success, setSuccess] = useState(false);

  const handleChange = (field: keyof TicketFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccess(false);

    if (!isOnline) {
      toast({
        title: "No Internet Connection",
        description: "Please check your connection and try again.",
        variant: "destructive"
      });
      return;
    }

    const ticketData: TicketCreateRequest = {
      title: formData.subject,
      description: formData.description,
      reporter_name: formData.name,
      reporter_email: formData.email,
      category: formData.category,
      priority: formData.priority,
      department: formData.department
    };

    createTicketMutation.mutate(ticketData, {
      onSuccess: (result) => {
        toast({
          title: "Ticket Submitted Successfully!",
          description: `Our IT team will contact you shortly. Ticket ID: ${result.id}`,
        });

        // Reset form
        setFormData({
          name: '',
          email: '',
          category: '',
          priority: 'medium' as const,
          subject: '',
          description: ''
        });
        setSuccess(true);
      }
    });
  };

  return (
    <Card className="w-full max-w-2xl mx-auto shadow-medium bg-gradient-card">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-bold text-foreground">Submit IT Support Ticket</CardTitle>
        <CardDescription className="text-muted-foreground flex items-center justify-center gap-2">
          Describe your issue and our AI will classify and route it to the right team
          {isOnline ? (
            <div className="flex items-center gap-1 text-green-600">
              <Wifi className="h-4 w-4" />
              <span className="text-xs">Online</span>
            </div>
          ) : (
            <div className="flex items-center gap-1 text-red-600">
              <WifiOff className="h-4 w-4" />
              <span className="text-xs">Offline</span>
            </div>
          )}
        </CardDescription>
        {success && (
          <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 rounded-md flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5" />
            <span>Your ticket was submitted successfully!</span>
          </div>
        )}  
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="flex items-center gap-2">
                <User className="w-4 h-4" />
                Full Name
              </Label>
              <Input
                id="name"
                placeholder="Your full name"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                required
                className="transition-all duration-300 focus:shadow-soft"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email" className="flex items-center gap-2">
                <Mail className="w-4 h-4" />
                Email Address
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                required
                className="transition-all duration-300 focus:shadow-soft"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Issue Category</Label>
              <Select value={formData.category} onValueChange={(value) => handleChange('category', value)}>
                <SelectTrigger className="transition-all duration-300 focus:shadow-soft">
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="hardware">Hardware Issues</SelectItem>
                  <SelectItem value="software">Software Problems</SelectItem>
                  <SelectItem value="network">Network/Connectivity</SelectItem>
                  <SelectItem value="email">Email Issues</SelectItem>
                  <SelectItem value="security">Security Concerns</SelectItem>
                  <SelectItem value="access">Access Rights</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Priority Level
              </Label>
              <Select value={formData.priority} onValueChange={(value) => handleChange('priority', value)}>
                <SelectTrigger className="transition-all duration-300 focus:shadow-soft">
                  <SelectValue placeholder="Select priority" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low - Can wait</SelectItem>
                  <SelectItem value="medium">Medium - Normal</SelectItem>
                  <SelectItem value="high">High - Urgent</SelectItem>
                  <SelectItem value="critical">Critical - Emergency</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="subject">Subject</Label>
            <Input
              id="subject"
              placeholder="Brief description of the issue"
              value={formData.subject}
              onChange={(e) => handleChange('subject', e.target.value)}
              required
              className="transition-all duration-300 focus:shadow-soft"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Detailed Description</Label>
            <Textarea
              id="description"
              placeholder="Please provide as much detail as possible about the issue you're experiencing..."
              rows={5}
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              required
              className="transition-all duration-300 focus:shadow-soft resize-none"
            />
          </div>

          <Button
            type="submit"
            variant="hero"
            size="lg"
            disabled={createTicketMutation.isPending || !isOnline}
            className="w-full"
          >
            {createTicketMutation.isPending ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                Submitting Ticket...
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Send className="w-4 h-4" />
                {isOnline ? 'Submit Support Ticket' : 'Offline - Cannot Submit'}
              </div>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};