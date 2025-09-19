'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Area, AreaChart 
} from 'recharts';
import { 
  Ticket, Clock, CheckCircle, AlertTriangle, Users, TrendingUp, Filter, 
  Search, RefreshCw, Zap, Shield, Activity, Brain, Sparkles, Globe
} from 'lucide-react';
import * as THREE from 'three';
import { Ticket as TicketType, DashboardStats } from '@/types/ticket';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    total_tickets: 0,
    open_tickets: 0,
    resolved_tickets: 0,
    avg_resolution_time: 0,
    success_rate: 0,
    categories: {},
    urgency_breakdown: {}
  });
  
  const [tickets, setTickets] = useState<TicketType[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);
  const mountRef = useRef<HTMLDivElement>(null);
  const frameRef = useRef<number | null>(null);

  // 3D Particle System Background
  useEffect(() => {
    if (!mountRef.current) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x000000, 0);
    mountRef.current.appendChild(renderer.domElement);

    // Create particle system
    const particlesGeometry = new THREE.BufferGeometry();
    const particlesCount = 2000;
    const posArray = new Float32Array(particlesCount * 3);

    for (let i = 0; i < particlesCount * 3; i++) {
      posArray[i] = (Math.random() - 0.5) * 100;
    }

    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    
    const particlesMaterial = new THREE.PointsMaterial({
      size: 0.3,
      color: 0x60a5fa,
      transparent: true,
      opacity: 0.8,
    });

    const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particlesMesh);

    // Add floating data nodes
    const nodeGeometry = new THREE.SphereGeometry(0.1, 8, 8);
    const nodes: THREE.Mesh[] = [];
    
    for (let i = 0; i < 50; i++) {
      const nodeMaterial = new THREE.MeshPhongMaterial({
        color: COLORS[i % COLORS.length],
        transparent: true,
        opacity: 0.6,
        emissive: COLORS[i % COLORS.length],
        emissiveIntensity: 0.2
      });
      
      const node = new THREE.Mesh(nodeGeometry, nodeMaterial);
      node.position.set(
        (Math.random() - 0.5) * 50,
        (Math.random() - 0.5) * 50,
        (Math.random() - 0.5) * 50
      );
      
      scene.add(node);
      nodes.push(node);
    }

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
    scene.add(ambientLight);
    
    const pointLight = new THREE.PointLight(0x60a5fa, 2, 100);
    pointLight.position.set(10, 10, 10);
    scene.add(pointLight);

    camera.position.z = 30;

    // Animation
    const animate = () => {
      frameRef.current = requestAnimationFrame(animate);
      
      particlesMesh.rotation.y += 0.001;
      particlesMesh.rotation.x += 0.0005;
      
      nodes.forEach((node, index) => {
        node.rotation.x += 0.01;
        node.rotation.y += 0.01;
        node.position.y += Math.sin(Date.now() * 0.001 + index) * 0.02;
      });
      
      camera.position.x = Math.sin(Date.now() * 0.0002) * 2;
      camera.lookAt(0, 0, 0);
      
      renderer.render(scene, camera);
    };
    
    animate();

    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
      window.removeEventListener('resize', handleResize);
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  // Mock data loading
  useEffect(() => {
    setTimeout(() => {
      setStats({
        total_tickets: 1247,
        open_tickets: 89,
        resolved_tickets: 1089,
        avg_resolution_time: 1.8,
        success_rate: 94.2,
        categories: {
          'Network/VPN': 342,
          'Email Systems': 278,
          'Hardware': 195,
          'Software': 187,
          'Security': 143,
          'Cloud Services': 102
        },
        urgency_breakdown: {
          'Critical': 23,
          'High': 67,
          'Medium': 298,
          'Low': 859
        }
      });

      setTickets([
        {
          id: 'TK-2024-001',
          source: 'email',
          text: 'VPN connection failing repeatedly during peak hours',
          language: 'English',
          category: 'Network/VPN',
          urgency: 'High',
          status: 'open',
          ai_response: 'Identified potential bandwidth congestion. Implementing load balancing...',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          user_email: 'rajesh.kumar@powergrid.com',
          user_name: 'Rajesh Kumar'
        },
        {
          id: 'TK-2024-002',
          source: 'glpi',
          text: 'Email server response bohot slow hai, urgent meeting ke liye chahiye',
          language: 'Hindi+English',
          category: 'Email Systems',
          urgency: 'Critical',
          status: 'in_progress',
          ai_response: 'Mail server optimization शुरू की गई है। 15 मिनट में resolve हो जाएगा।',
          created_at: new Date(Date.now() - 1800000).toISOString(),
          updated_at: new Date().toISOString(),
          user_email: 'priya.sharma@powergrid.com',
          user_name: 'Priya Sharma'
        }
      ]);

      setIsLoading(false);
    }, 2000);
  }, []);

  const categoryData = Object.entries(stats.categories).map(([name, value]) => ({ name, value }));
  const urgencyData = Object.entries(stats.urgency_breakdown).map(([name, value]) => ({ name, value }));
  
  const trendData = [
    { name: 'Mon', tickets: 45, resolved: 42 },
    { name: 'Tue', tickets: 52, resolved: 48 },
    { name: 'Wed', tickets: 48, resolved: 46 },
    { name: 'Thu', tickets: 61, resolved: 58 },
    { name: 'Fri', tickets: 55, resolved: 52 },
    { name: 'Sat', tickets: 28, resolved: 26 },
    { name: 'Sun', tickets: 22, resolved: 21 }
  ];

  const filteredTickets = tickets.filter(ticket => {
    const matchesSearch = ticket.text.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         ticket.user_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         ticket.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'all' || ticket.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'bg-gradient-to-r from-red-500 to-pink-500 text-white';
      case 'in_progress': return 'bg-gradient-to-r from-yellow-500 to-orange-500 text-white';
      case 'resolved': return 'bg-gradient-to-r from-green-500 to-emerald-500 text-white';
      case 'closed': return 'bg-gradient-to-r from-gray-500 to-slate-500 text-white';
      default: return 'bg-gradient-to-r from-gray-400 to-gray-500 text-white';
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'Critical': return 'bg-gradient-to-r from-red-600 to-red-700 text-white shadow-lg shadow-red-500/30';
      case 'High': return 'bg-gradient-to-r from-orange-500 to-orange-600 text-white shadow-lg shadow-orange-500/30';
      case 'Medium': return 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/30';
      case 'Low': return 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-lg shadow-green-500/30';
      default: return 'bg-gradient-to-r from-gray-500 to-gray-600 text-white';
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center relative overflow-hidden">
        <div ref={mountRef} className="absolute inset-0" />
        <div className="relative z-10 text-center">
          <div className="mb-8">
            <div className="w-20 h-20 mx-auto mb-4 relative">
              <div className="w-20 h-20 rounded-full border-4 border-blue-500/30 border-t-blue-500 animate-spin"></div>
              <Brain className="w-8 h-8 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-blue-400 animate-pulse" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Initializing AI Dashboard</h2>
            <p className="text-blue-300">Loading real-time analytics...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
      {/* 3D Background */}
      <div ref={mountRef} className="absolute inset-0 z-0" />
      
      {/* Glassmorphism Overlay */}
      <div className="absolute inset-0 z-10 bg-gradient-to-br from-blue-500/5 via-purple-500/10 to-cyan-500/5 backdrop-blur-sm" />
      
      {/* Content */}
      <div className="relative z-20 p-6">
        {/* Header */}
        <div className="mb-8 backdrop-blur-xl bg-white/10 rounded-3xl p-6 border border-white/20 shadow-2xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl shadow-lg">
                <Activity className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white mb-1 flex items-center gap-2">
                  IT Command Center
                  <Sparkles className="w-6 h-6 text-yellow-400 animate-pulse" />
                </h1>
                <p className="text-blue-200">Real-time Intelligence Dashboard</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 bg-green-500/20 px-3 py-1 rounded-full">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-green-300 text-sm">Live</span>
              </div>
              <button className="p-2 bg-white/10 hover:bg-white/20 rounded-xl transition-all duration-300 backdrop-blur-sm">
                <RefreshCw className="w-5 h-5 text-white hover:rotate-180 transition-transform duration-500" />
              </button>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[
            { 
              title: 'Total Tickets', 
              value: stats.total_tickets.toLocaleString(), 
              icon: Ticket, 
              color: 'from-blue-500 to-cyan-500',
              trend: '+12%'
            },
            { 
              title: 'Active Issues', 
              value: stats.open_tickets, 
              icon: AlertTriangle, 
              color: 'from-red-500 to-pink-500',
              trend: '-8%'
            },
            { 
              title: 'Avg Resolution', 
              value: `${stats.avg_resolution_time}h`, 
              icon: Clock, 
              color: 'from-purple-500 to-indigo-500',
              trend: '-15%'
            },
            { 
              title: 'Success Rate', 
              value: `${stats.success_rate}%`, 
              icon: TrendingUp, 
              color: 'from-green-500 to-emerald-500',
              trend: '+3%'
            }
          ].map((stat, index) => (
            <div 
              key={stat.title}
              className="backdrop-blur-xl bg-white/10 p-6 rounded-2xl shadow-xl border border-white/20 hover:bg-white/15 transition-all duration-300 transform hover:scale-105 hover:shadow-2xl"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 bg-gradient-to-r ${stat.color} rounded-xl shadow-lg`}>
                  <stat.icon className="w-6 h-6 text-white" />
                </div>
                <div className={`px-2 py-1 rounded-full text-xs font-semibold ${
                  stat.trend.startsWith('+') ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'
                }`}>
                  {stat.trend}
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-white/70 mb-1">{stat.title}</p>
                <p className="text-3xl font-bold text-white">{stat.value}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Category Chart */}
          <div className="backdrop-blur-xl bg-white/10 p-6 rounded-2xl shadow-xl border border-white/20">
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <BarChart className="w-6 h-6 text-blue-400" />
              Tickets by Category
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={categoryData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis 
                  dataKey="name" 
                  angle={-45} 
                  textAnchor="end" 
                  height={80} 
                  stroke="rgba(255,255,255,0.7)"
                  fontSize={12}
                />
                <YAxis stroke="rgba(255,255,255,0.7)" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(0,0,0,0.8)', 
                    border: 'none', 
                    borderRadius: '12px',
                    backdropFilter: 'blur(10px)'
                  }} 
                />
                <Bar 
                  dataKey="value" 
                  fill="url(#gradient1)" 
                  radius={[4, 4, 0, 0]}
                  animationBegin={0}
                  animationDuration={1000}
                />
                <defs>
                  <linearGradient id="gradient1" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3B82F6" stopOpacity={1}/>
                    <stop offset="100%" stopColor="#1D4ED8" stopOpacity={0.8}/>
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Urgency Distribution */}
          <div className="backdrop-blur-xl bg-white/10 p-6 rounded-2xl shadow-xl border border-white/20">
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Zap className="w-6 h-6 text-yellow-400" />
              Priority Distribution
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={urgencyData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => {
                    // Recharts' label param types may be loose; guard at runtime and coerce to number
                    const name = (entry as any).name ?? '';
                    const rawPercent = (entry as any).percent;
                    const percent = typeof rawPercent === 'number' ? rawPercent : 0;
                    return `${name} ${(percent * 100).toFixed(0)}%`;
                  }}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                  animationBegin={0}
                  animationDuration={1000}
                >
                  {urgencyData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(0,0,0,0.8)', 
                    border: 'none', 
                    borderRadius: '12px',
                    backdropFilter: 'blur(10px)'
                  }} 
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Trend Chart */}
        <div className="backdrop-blur-xl bg-white/10 p-6 rounded-2xl shadow-xl border border-white/20 mb-8">
          <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-green-400" />
            Weekly Performance Trend
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="name" stroke="rgba(255,255,255,0.7)" />
              <YAxis stroke="rgba(255,255,255,0.7)" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(0,0,0,0.8)', 
                  border: 'none', 
                  borderRadius: '12px',
                  backdropFilter: 'blur(10px)'
                }} 
              />
              <Area 
                type="monotone" 
                dataKey="tickets" 
                stackId="1"
                stroke="#F59E0B" 
                fill="url(#gradient2)" 
                animationDuration={1500}
              />
              <Area 
                type="monotone" 
                dataKey="resolved" 
                stackId="2"
                stroke="#10B981" 
                fill="url(#gradient3)" 
                animationDuration={1500}
              />
              <defs>
                <linearGradient id="gradient2" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#F59E0B" stopOpacity={0.6}/>
                  <stop offset="100%" stopColor="#F59E0B" stopOpacity={0.1}/>
                </linearGradient>
                <linearGradient id="gradient3" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10B981" stopOpacity={0.6}/>
                  <stop offset="100%" stopColor="#10B981" stopOpacity={0.1}/>
                </linearGradient>
              </defs>
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Tickets Table */}
        <div className="backdrop-blur-xl bg-white/10 rounded-2xl shadow-xl border border-white/20 overflow-hidden">
          <div className="p-6 border-b border-white/10">
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <Shield className="w-6 h-6 text-purple-400" />
                Active Tickets Monitor
              </h3>
              
              <div className="flex gap-3">
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50" />
                  <input
                    type="text"
                    placeholder="Search tickets..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 pr-4 py-2 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500/50 backdrop-blur-sm"
                  />
                </div>
                
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 bg-white/10 border border-white/20 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 backdrop-blur-sm"
                >
                  <option value="all" className="bg-slate-800">All Status</option>
                  <option value="open" className="bg-slate-800">Open</option>
                  <option value="in_progress" className="bg-slate-800">In Progress</option>
                  <option value="resolved" className="bg-slate-800">Resolved</option>
                  <option value="closed" className="bg-slate-800">Closed</option>
                </select>
              </div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5">
                <tr>
                  {['Ticket ID', 'User', 'Issue Description', 'Category', 'Priority', 'Status', 'Created'].map((header) => (
                    <th key={header} className="px-6 py-4 text-left text-xs font-semibold text-white/70 uppercase tracking-wider">
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {filteredTickets.map((ticket, index) => (
                  <tr 
                    key={ticket.id} 
                    className="hover:bg-white/5 transition-all duration-300 transform hover:scale-[1.01]"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <td className="px-6 py-4 text-sm font-mono text-blue-300">{ticket.id}</td>
                    <td className="px-6 py-4 text-sm text-white">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
                          {ticket.user_name?.charAt(0)}
                        </div>
                        {ticket.user_name}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-white/90 max-w-xs">
                      <div className="truncate" title={ticket.text}>
                        {ticket.text}
                      </div>
                      <div className="text-xs text-white/50 mt-1">
                        {ticket.language}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span className="px-3 py-1 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 rounded-full text-cyan-300 text-xs">
                        {ticket.category}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 text-xs rounded-full font-semibold ${getUrgencyColor(ticket.urgency)}`}>
                        {ticket.urgency}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 text-xs rounded-full font-semibold ${getStatusColor(ticket.status)}`}>
                        {ticket.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-white/70">
                      {new Date(ticket.created_at).toLocaleDateString('en-IN', {
                        day: '2-digit',
                        month: 'short',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredTickets.length === 0 && (
            <div className="p-12 text-center">
              <Globe className="w-12 h-12 text-white/30 mx-auto mb-4" />
              <p className="text-white/60">No tickets match your current filters</p>
            </div>
          )}
        </div>

        {/* Footer Stats */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { label: 'AI Resolution Rate', value: '87%', icon: Brain },
            { label: 'Avg Response Time', value: '2.3min', icon: Zap },
            { label: 'Customer Satisfaction', value: '4.8/5', icon: Sparkles }
          ].map((metric, index) => (
            <div 
              key={metric.label}
              className="backdrop-blur-xl bg-white/5 p-4 rounded-xl border border-white/10 flex items-center gap-3"
            >
              <metric.icon className="w-6 h-6 text-blue-400" />
              <div>
                <p className="text-white/60 text-sm">{metric.label}</p>
                <p className="text-white font-bold text-lg">{metric.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fade-in-up {
          animation: fadeInUp 0.6s ease-out forwards;
        }
      `}</style>
    </div>
  );
}