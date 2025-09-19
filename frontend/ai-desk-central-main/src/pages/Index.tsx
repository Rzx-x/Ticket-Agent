import React from 'react';
import { Button } from '@/components/ui/button';
import { TicketForm } from '@/components/TicketForm';
import { Card, CardContent } from '@/components/ui/card';
import { Link } from 'react-router-dom';
import { 
  Shield, 
  Zap, 
  Globe, 
  BarChart3, 
  Users, 
  Clock, 
  MessageCircle,
  Settings,
  ChevronRight
} from 'lucide-react';
import heroImage from '@/assets/hero-bg.jpg';

const Index = () => {
  const features = [
    {
      icon: <Zap className="w-6 h-6" />,
      title: "AI-Powered Classification",
      description: "Smart categorization and priority detection using Claude AI"
    },
    {
      icon: <Globe className="w-6 h-6" />,
      title: "Multi-Language Support", 
      description: "Automatic language detection and responses in English & Hindi"
    },
    {
      icon: <MessageCircle className="w-6 h-6" />,
      title: "Auto-Response System",
      description: "Instant acknowledgment and initial troubleshooting guidance"
    },
    {
      icon: <BarChart3 className="w-6 h-6" />,
      title: "Real-Time Analytics",
      description: "Live dashboard with ticket metrics and performance insights"
    },
    {
      icon: <Users className="w-6 h-6" />,
      title: "Team Collaboration", 
      description: "Seamless handoff to IT staff with full context preservation"
    },
    {
      icon: <Clock className="w-6 h-6" />,
      title: "Fast Resolution",
      description: "Reduced response times through intelligent routing"
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-gradient-card shadow-soft sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-primary rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">OmniDesk AI</h1>
              <p className="text-xs text-muted-foreground">Smart IT Ticket Hub</p>
            </div>
          </div>
          <Link to="/admin">
            <Button variant="professional" className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              IT Admin Panel
              <ChevronRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-20 overflow-hidden">
        <div 
          className="absolute inset-0 opacity-10 bg-cover bg-center"
          style={{ backgroundImage: `url(${heroImage})` }}
        />
        <div className="absolute inset-0 bg-gradient-hero opacity-90" />
        <div className="relative container mx-auto px-4 text-center">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-5xl md:text-6xl font-bold text-primary-foreground mb-6 leading-tight">
              Intelligent IT Support
              <span className="block text-primary-glow">Powered by AI</span>
            </h2>
            <p className="text-xl text-primary-foreground/90 mb-8 leading-relaxed">
              Streamline your IT helpdesk with automated ticket classification, 
              multilingual support, and intelligent routing. Get faster resolutions 
              and happier users.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button variant="hero" size="lg" className="shadow-glow">
                <Zap className="w-5 h-5" />
                Get Started
              </Button>
              <Button variant="professional" size="lg" className="bg-white/20 hover:bg-white/30 text-white border-white/30">
                Learn More
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gradient-subtle">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h3 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Why Choose OmniDesk AI?
            </h3>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Transform your IT support with cutting-edge AI technology and seamless integrations
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="shadow-medium bg-gradient-card hover:shadow-strong transition-all duration-300 group">
                <CardContent className="p-6">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-all duration-300">
                    {feature.icon}
                  </div>
                  <h4 className="text-xl font-semibold text-foreground mb-2">
                    {feature.title}
                  </h4>
                  <p className="text-muted-foreground">
                    {feature.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Ticket Submission Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h3 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Need IT Support?
            </h3>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Submit your ticket below and our AI will analyze and route it to the right team. 
              You'll receive an immediate response with next steps.
            </p>
          </div>
          
          <TicketForm />
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gradient-card border-t py-12">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="flex items-center gap-3 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                <Shield className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <p className="font-semibold text-foreground">OmniDesk AI</p>
                <p className="text-xs text-muted-foreground">Smart IT Ticket Hub</p>
              </div>
            </div>
            <div className="text-center md:text-right">
              <p className="text-sm text-muted-foreground">
                © 2024 OmniDesk AI. Streamlining IT support with intelligence.
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;
