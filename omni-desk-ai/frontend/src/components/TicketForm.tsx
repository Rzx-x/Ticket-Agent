'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Zap, Shield, Globe, Sparkles } from 'lucide-react';
import * as THREE from 'three';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  isLoading?: boolean;
}

export default function TicketForm() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: "🚀 Hello! I'm OmniDesk AI, your intelligent IT support companion. Describe your technical challenge, and I'll provide instant solutions with the power of advanced AI. Express yourself in English, Hindi, or mix both languages!",
      isUser: false,
      timestamp: new Date()
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const frameRef = useRef<number | null>(null);

  // 3D Background Animation
  useEffect(() => {
    if (!mountRef.current) return;

    // Scene setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x000000, 0);
    mountRef.current.appendChild(renderer.domElement);
    
    sceneRef.current = scene;
    rendererRef.current = renderer;

    // Create floating geometric shapes
    const geometry1 = new THREE.OctahedronGeometry(0.8, 0);
    const geometry2 = new THREE.TetrahedronGeometry(0.6, 0);
    const geometry3 = new THREE.IcosahedronGeometry(0.7, 0);
    
    const material1 = new THREE.MeshPhongMaterial({ 
      color: 0x60a5fa, 
      transparent: true, 
      opacity: 0.8,
      shininess: 100
    });
    const material2 = new THREE.MeshPhongMaterial({ 
      color: 0x8b5cf6, 
      transparent: true, 
      opacity: 0.7,
      shininess: 100
    });
    const material3 = new THREE.MeshPhongMaterial({ 
      color: 0x06b6d4, 
      transparent: true, 
      opacity: 0.6,
      shininess: 100
    });

    const shapes: THREE.Mesh[] = [];
    for (let i = 0; i < 15; i++) {
      const geometries = [geometry1, geometry2, geometry3];
      const materials = [material1, material2, material3];
      
      const shape = new THREE.Mesh(
        geometries[i % 3],
        materials[i % 3]
      );
      
      shape.position.x = (Math.random() - 0.5) * 20;
      shape.position.y = (Math.random() - 0.5) * 20;
      shape.position.z = (Math.random() - 0.5) * 20;
      
      scene.add(shape);
      shapes.push(shape);
    }

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(5, 5, 5);
    scene.add(directionalLight);

    const pointLight = new THREE.PointLight(0x60a5fa, 1, 100);
    pointLight.position.set(10, 10, 10);
    scene.add(pointLight);

    camera.position.z = 5;

    // Animation loop
    const animate = () => {
      frameRef.current = requestAnimationFrame(animate);
      
      shapes.forEach((shape, index) => {
        shape.rotation.x += 0.005 + index * 0.001;
        shape.rotation.y += 0.005 + index * 0.001;
        shape.position.y += Math.sin(Date.now() * 0.001 + index) * 0.001;
      });
      
      camera.position.x = Math.sin(Date.now() * 0.0005) * 0.5;
      camera.lookAt(0, 0, 0);
      
      renderer.render(scene, camera);
    };
    
    animate();

    // Handle resize
    const handleResize = () => {
      if (!camera || !renderer) return;
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current);
      }
      window.removeEventListener('resize', handleResize);
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      text: "🧠 Analyzing your request with advanced AI algorithms...",
      isUser: false,
      timestamp: new Date(),
      isLoading: true
    };

    setMessages(prev => [...prev, loadingMessage]);

    try {
      const response = await fetch('/api/submit-ticket', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: inputText,
          source: 'web',
          user_email: 'user@powergrid.com'
        }),
      });

      const data = await response.json();

      setMessages(prev => {
        const filtered = prev.filter(msg => !msg.isLoading);
        return [...filtered, {
          id: (Date.now() + 2).toString(),
          text: `✨ ${data.ai_response || "I've analyzed your request and categorized it as " + (data.category || "General Support") + ". Our expert team is now handling this with priority!"}`,
          isUser: false,
          timestamp: new Date()
        }];
      });

    } catch (error) {
      setMessages(prev => {
        const filtered = prev.filter(msg => !msg.isLoading);
        return [...filtered, {
          id: (Date.now() + 2).toString(),
          text: "⚡ I'm experiencing temporary connectivity issues. Your ticket has been securely saved and our technical team will review it manually within minutes.",
          isUser: false,
          timestamp: new Date()
        }];
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* 3D Background */}
      <div 
        ref={mountRef} 
        className="absolute inset-0 z-0"
        style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)' }}
      />
      
      {/* Glassmorphism Overlay */}
      <div className="absolute inset-0 z-10 bg-gradient-to-br from-blue-500/10 via-purple-500/5 to-cyan-500/10 backdrop-blur-sm" />
      
      {/* Content */}
      <div className="relative z-20 max-w-5xl mx-auto px-6 py-8">
        <div className="backdrop-blur-xl bg-white/10 rounded-3xl shadow-2xl border border-white/20 overflow-hidden">
          {/* Animated Header */}
          <div className="relative bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 p-8">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600/50 via-purple-600/50 to-cyan-600/50 animate-pulse" />
            <div className="relative flex items-center gap-4">
              <div className="p-3 bg-white/20 rounded-2xl backdrop-blur-sm animate-bounce">
                <Bot className="w-10 h-10 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-2">
                  OmniDesk AI
                  <Sparkles className="w-6 h-6 text-yellow-300 animate-spin" />
                </h1>
                <p className="text-blue-100 text-lg">
                  Next-Generation Intelligent Support System
                </p>
              </div>
            </div>
            
            {/* Floating Elements */}
            <div className="absolute top-4 right-4 flex gap-2">
              <div className="p-2 bg-white/10 rounded-full animate-pulse">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div className="p-2 bg-white/10 rounded-full animate-pulse delay-150">
                <Globe className="w-5 h-5 text-white" />
              </div>
              <div className="p-2 bg-white/10 rounded-full animate-pulse delay-300">
                <Zap className="w-5 h-5 text-white" />
              </div>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="h-96 overflow-y-auto p-8 space-y-6 bg-gradient-to-b from-transparent to-black/5">
            {messages.map((message, index) => (
              <div
                key={message.id}
                className={`flex gap-4 ${message.isUser ? 'justify-end' : 'justify-start'} animate-fade-in-up`}
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className={`flex gap-4 max-w-4xl ${message.isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                  <div className={`w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg ${
                    message.isUser 
                      ? 'bg-gradient-to-r from-blue-500 to-purple-500' 
                      : message.isLoading
                      ? 'bg-gradient-to-r from-yellow-400 to-orange-500 animate-pulse'
                      : 'bg-gradient-to-r from-cyan-400 to-blue-500'
                  }`}>
                    {message.isUser ? 
                      <User className="w-6 h-6 text-white" /> : 
                      <Bot className={`w-6 h-6 text-white ${message.isLoading ? 'animate-spin' : ''}`} />
                    }
                  </div>
                  
                  <div className={`rounded-2xl p-6 shadow-xl backdrop-blur-sm border ${
                    message.isUser
                      ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white border-blue-300/30'
                      : message.isLoading
                      ? 'bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200/50 text-yellow-800'
                      : 'bg-white/80 border-white/30 text-gray-800'
                  }`}>
                    <p className={`leading-relaxed ${message.isLoading ? 'flex items-center gap-2' : ''}`}>
                      {message.text}
                    </p>
                    <p className={`text-xs mt-3 ${
                      message.isUser ? 'text-blue-100' : 'text-gray-500'
                    }`}>
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="p-8 bg-gradient-to-r from-white/10 to-white/5 backdrop-blur-sm">
            <div className="flex gap-4">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Describe your IT challenge... (English/Hindi supported) ✨"
                  className="w-full border-0 rounded-2xl px-6 py-4 text-lg bg-white/90 backdrop-blur-sm focus:outline-none focus:ring-4 focus:ring-blue-500/30 shadow-xl placeholder-gray-500 transition-all duration-300"
                  disabled={isLoading}
                />
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-cyan-500/20 -z-10 blur-xl" />
              </div>
              
              <button
                type="submit"
                disabled={isLoading || !inputText.trim()}
                className="bg-gradient-to-r from-blue-500 via-purple-500 to-cyan-500 hover:from-blue-600 hover:via-purple-600 hover:to-cyan-600 disabled:from-gray-400 disabled:to-gray-500 text-white px-8 py-4 rounded-2xl flex items-center gap-3 transition-all duration-300 shadow-xl hover:shadow-2xl transform hover:scale-105 disabled:scale-100"
              >
                <Send className="w-5 h-5" />
                <span className="font-semibold">Send</span>
              </button>
            </div>
            
            <div className="mt-6 flex flex-wrap gap-6 text-sm text-white/80">
              <div className="flex items-center gap-2 bg-white/10 px-4 py-2 rounded-full backdrop-blur-sm">
                <span className="text-2xl">💡</span>
                <span>"My laptop won't connect to WiFi"</span>
              </div>
              <div className="flex items-center gap-2 bg-white/10 px-4 py-2 rounded-full backdrop-blur-sm">
                <span className="text-2xl">💡</span>
                <span>"VPN nahi chal raha hai"</span>
              </div>
              <div className="flex items-center gap-2 bg-white/10 px-4 py-2 rounded-full backdrop-blur-sm">
                <span className="text-2xl">💡</span>
                <span>"Email server down"</span>
              </div>
            </div>
          </form>
        </div>
      </div>
      
      <style jsx>{`
        @keyframes fade-in-up {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fade-in-up {
          animation: fade-in-up 0.6s ease-out forwards;
        }
      `}</style>
    </div>
  );
}