import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { Send, User, Mail, AlertTriangle } from 'lucide-react';

interface TicketFormData {
  name: string;
  email: string;
  category: string;
  priority: string;
  subject: string;
  description: string;
}

export const TicketForm = () => {
  const { toast } = useToast();
  const [formData, setFormData] = useState<TicketFormData>({
    name: '',
    email: '',
    category: '',
    priority: '',
    subject: '',
    description: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (field: keyof TicketFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));

    toast({
      title: "Ticket Submitted Successfully!",
      description: "Our IT team will contact you shortly. Ticket ID: #TK-" + Math.random().toString(36).substr(2, 6).toUpperCase(),
    });

    // Reset form
    setFormData({
      name: '',
      email: '',
      category: '',
      priority: '',
      subject: '',
      description: ''
    });
    setIsSubmitting(false);
  };

  return (
    <Card className="w-full max-w-2xl mx-auto shadow-medium bg-gradient-card">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-bold text-foreground">Submit IT Support Ticket</CardTitle>
        <CardDescription className="text-muted-foreground">
          Describe your issue and our AI will classify and route it to the right team
        </CardDescription>
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
            disabled={isSubmitting}
            className="w-full"
          >
            {isSubmitting ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                Submitting Ticket...
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Send className="w-4 h-4" />
                Submit Support Ticket
              </div>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};