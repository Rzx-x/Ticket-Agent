"use client";

import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { BarChart3, Zap, Shield, Globe, Brain, Sparkles, ArrowRight, Play } from 'lucide-react';
import TicketForm from '@/components/TicketForm';
import Link from 'next/link';

export default function Home() {
  const mountRef = useRef<HTMLDivElement>(null);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    if (!mountRef.current) return;

    let animationFrameId: number;
    const currentMount = mountRef.current;

    // Scene setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    currentMount.appendChild(renderer.domElement);

    // Particles
    const particleCount = 1000;
    const particles = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    const color1 = new THREE.Color(0x3b82f6); // Blue
    const color2 = new THREE.Color(0x8b5cf6); // Purple
    const color3 = new THREE.Color(0x06b6d4); // Cyan

    for (let i = 0; i < particleCount; i++) {
      // Position
      positions[i * 3] = (Math.random() - 0.5) * 200;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 200;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 200;

      // Color
      const mixedColor = new THREE.Color();
      mixedColor.lerpColors(color1, color2, Math.random());
      mixedColor.lerp(color3, Math.random());
      colors[i * 3] = mixedColor.r;
      colors[i * 3 + 1] = mixedColor.g;
      colors[i * 3 + 2] = mixedColor.b;
    }

    particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particles.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const particleMaterial = new THREE.PointsMaterial({
      size: 0.5,
      vertexColors: true,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true
    });

    const particleSystem = new THREE.Points(particles, particleMaterial);
    scene.add(particleSystem);

    // Lines
    const lineMaterial = new THREE.LineBasicMaterial({
      color: 0x3b82f6,
      transparent: true,
      opacity: 0.1,
      blending: THREE.AdditiveBlending
    });
    const lineGeometry = new THREE.BufferGeometry();
    const linePositions = new Float32Array(particleCount * 3 * 2); // Each particle can connect to one other
    lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    const lines = new THREE.LineSegments(lineGeometry, lineMaterial);
    scene.add(lines);

    // Camera position
    camera.position.z = 50;

    // Animation loop
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      // Rotate particles
      particleSystem.rotation.x += 0.0005;
      particleSystem.rotation.y += 0.0008;

      // Update line connections (simplified for performance)
      const currentLinePositions = lines.geometry.attributes.position.array as Float32Array;
      let lineIndex = 0;
      for (let i = 0; i < particleCount; i += 2) { // Connect every other particle
        if (i + 1 < particleCount) {
          currentLinePositions[lineIndex++] = positions[i * 3];
          currentLinePositions[lineIndex++] = positions[i * 3 + 1];
          currentLinePositions[lineIndex++] = positions[i * 3 + 2];

          currentLinePositions[lineIndex++] = positions[(i + 1) * 3];
          currentLinePositions[lineIndex++] = positions[(i + 1) * 3 + 1];
          currentLinePositions[lineIndex++] = positions[(i + 1) * 3 + 2];
        }
      }
      lines.geometry.attributes.position.needsUpdate = true;

      renderer.render(scene, camera);
    };

    animate();

    // Handle window resize
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      currentMount.removeChild(renderer.domElement);
      window.removeEventListener('resize', handleResize);
    };
  }, [isMounted]); // Rerun effect if isMounted changes

  if (!isMounted) {
    return null; // Render nothing on the server
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
      {/* Three.js Background */}
      <div ref={mountRef} className="absolute inset-0 z-0"></div>

      {/* Navigation */}
      <nav className="relative z-10 backdrop-blur-xl bg-white/5 border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl">
                <Brain className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">OmniDesk AI</h1>
                <span className="text-xs text-blue-300 font-medium">POWERGRID Intelligence</span>
              </div>
            </div>
            
            <Link 
              href="/dashboard"
              className="group flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-xl"
            >
              <BarChart3 className="w-5 h-5" />
              <span>IT Command Center</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-8">
        {/* Main Hero */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-500/20 to-purple-500/20 backdrop-blur-sm border border-blue-500/30 rounded-full px-6 py-2 mb-8">
            <Sparkles className="w-4 h-4 text-yellow-400 animate-spin" />
            <span className="text-blue-300 font-medium">Next-Gen AI Support System</span>
            <Sparkles className="w-4 h-4 text-yellow-400 animate-spin" />
          </div>
          
          <h1 className="text-6xl md:text-7xl font-bold text-white mb-8 leading-tight">
            <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
              Intelligent IT
            </span>
            <br />
            <span className="text-white">Support Revolution</span>
          </h1>
          
          <p className="text-xl md:text-2xl text-white/80 max-w-4xl mx-auto mb-12 leading-relaxed">
            Experience the future of technical support with our AI-powered assistant that understands 
            <span className="text-blue-400 font-semibold"> English & Hindi</span>, provides 
            <span className="text-purple-400 font-semibold"> instant solutions</span>, and connects you with 
            <span className="text-cyan-400 font-semibold"> expert engineers</span> seamlessly.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-6 justify-center mb-16">
            <button className="group px-8 py-4 bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 hover:from-blue-700 hover:via-purple-700 hover:to-cyan-700 text-white font-bold text-lg rounded-2xl transition-all duration-300 transform hover:scale-105 shadow-xl hover:shadow-2xl">
              <span className="flex items-center gap-3">
                Start Support Chat
                <Zap className="w-5 h-5 group-hover:animate-bounce" />
              </span>
            </button>
            
            <button className="group px-8 py-4 bg-white/10 hover:bg-white/20 border border-white/30 text-white font-semibold text-lg rounded-2xl transition-all duration-300 backdrop-blur-sm">
              <span className="flex items-center gap-3">
                <Play className="w-5 h-5" />
                Watch Demo
              </span>
            </button>
          </div>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          {[
            {
              icon: Brain,
              title: "AI-Powered Intelligence",
              description: "Advanced machine learning algorithms provide instant, contextual solutions to technical challenges",
              color: "from-blue-500 to-cyan-500",
              delay: "0ms"
            },
            {
              icon: Globe,
              title: "Multi-Language Support",
              description: "Seamlessly communicate in English, Hindi, or mix both languages for natural conversation",
              color: "from-purple-500 to-pink-500",
              delay: "200ms"
            },
            {
              icon: Shield,
              title: "Enterprise Security",
              description: "Military-grade encryption and compliance with POWERGRID's security protocols",
              color: "from-green-500 to-emerald-500",
              delay: "400ms"
            }
          ].map((feature, index) => (
            <div 
              key={feature.title}
              className="group relative backdrop-blur-xl bg-white/5 rounded-2xl p-8 border border-white/20 hover:bg-white/10 transition-all duration-500 transform hover:scale-105 hover:-translate-y-2"
              style={{ animationDelay: feature.delay }}
            >
              <div className="absolute inset-0 bg-gradient-to-r opacity-0 group-hover:opacity-10 rounded-2xl transition-opacity duration-500" style={{ background: `linear-gradient(45deg, ${feature.color.split(' ')[1]}, ${feature.color.split(' ')[3]})` }}></div>
              
              <div className="relative">
                <div className={`w-16 h-16 bg-gradient-to-r ${feature.color} rounded-2xl flex items-center justify-center mb-6 shadow-lg group-hover:shadow-xl transition-all duration-300`}>
                  <feature.icon className="w-8 h-8 text-white" />
                </div>
                
                <h3 className="text-xl font-bold text-white mb-4 group-hover:text-blue-300 transition-colors">
                  {feature.title}
                </h3>
                
                <p className="text-white/70 leading-relaxed group-hover:text-white/90 transition-colors">
                  {feature.description}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Stats Section */}
        <div className="backdrop-blur-xl bg-white/5 rounded-3xl p-8 border border-white/20 mb-16">
          <h2 className="text-3xl font-bold text-white text-center mb-12">
            Powering POWERGRID's Digital Transformation
          </h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { number: "10,000+", label: "Issues Resolved", icon: "🎯" },
              { number: "98.5%", label: "Success Rate", icon: "📈" },
              { number: "< 2min", label: "Avg Response", icon: "⚡" },
              { number: "24/7", label: "Availability", icon: "🌟" }
            ].map((stat, index) => (
              <div key={stat.label} className="text-center group">
                <div className="text-4xl mb-2">{stat.icon}</div>
                <div className="text-3xl md:text-4xl font-bold text-white mb-2 group-hover:text-blue-400 transition-colors">
                  {stat.number}
                </div>
                <div className="text-white/70 group-hover:text-white transition-colors">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Main Ticket Form */}
        <TicketForm />

        {/* Technology Showcase */}
        <div className="mt-16 text-center">
          <h2 className="text-2xl font-bold text-white mb-8">Powered by Cutting-Edge Technology</h2>
          <div className="flex flex-wrap justify-center items-center gap-8 opacity-60">
            {['Claude AI', 'TensorFlow', 'Three.js', 'Next.js', 'Postgres', 'Qdrant'].map((tech) => (
              <div key={tech} className="px-4 py-2 bg-white/5 rounded-lg border border-white/10">
                <span className="text-white/80 font-medium">{tech}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-16 pt-8 border-t border-white/10 text-center">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-white/60">
              <p>© 2024 OmniDesk AI • Built for POWERGRID Corporation</p>
            </div>
            
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2 text-green-400">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm">All Systems Operational</span>
              </div>
              
              <div className="text-white/60 text-sm">
                Emergency: <span className="font-mono text-white">1800-POWERGRID</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }
        
        .animate-float {
          animation: float 6s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
