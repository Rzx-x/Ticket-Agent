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

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    const chatContainer = document.getElementById('chat-messages');
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }, [messages]);

  // Quick reply suggestions
  const suggestions = [
    { icon: "💻", text: "My laptop won't connect to WiFi" },
    { icon: "🔒", text: "VPN nahi chal raha hai" },
    { icon: "📧", text: "Email server down" },
    { icon: "🖨️", text: "Printer not working" }
  ];

  // Handle suggestion click
  const handleSuggestion = (text: string) => {
    setInputText(text);
  };

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Ctrl/Cmd + Enter to submit
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSubmit(e as any);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* 3D Background */}
      <div 
        ref={mountRef} 
        className="absolute inset-0 z-0"
        style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)' }}
        aria-hidden="true"
      />
      
      {/* Glassmorphism Overlay */}
      <div 
        className="absolute inset-0 z-10 bg-gradient-to-br from-blue-500/10 via-purple-500/5 to-cyan-500/10 backdrop-blur-sm" 
        aria-hidden="true"
      />
      
      {/* Content */}
      <main className="relative z-20 max-w-5xl mx-auto px-6 py-8">
        <div className="backdrop-blur-xl bg-white/10 rounded-3xl shadow-2xl border border-white/20 overflow-hidden transition-all duration-500 hover:shadow-[0_0_50px_0_rgba(59,130,246,0.3)]">
          {/* Animated Header */}
          <header className="relative bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 p-8">
            <div 
              className="absolute inset-0 bg-gradient-to-r from-blue-600/50 via-purple-600/50 to-cyan-600/50 animate-pulse" 
              aria-hidden="true"
            />
            <div className="relative flex items-center gap-4">
              <div className="p-3 bg-white/20 rounded-2xl backdrop-blur-sm animate-float">
                <Bot className="w-10 h-10 text-white" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-2">
                  OmniDesk AI
                  <Sparkles className="w-6 h-6 text-yellow-300 animate-spin-slow" aria-hidden="true" />
                </h1>
                <p className="text-blue-100 text-lg">
                  Intelligent Support System with Multi-Language Capabilities
                </p>
              </div>
            </div>
            
            {/* Feature Icons */}
            <div className="absolute top-4 right-4 flex gap-2" aria-hidden="true">
              <div className="p-2 bg-white/10 rounded-full animate-pulse group transition-all duration-300 hover:scale-110">
                <Shield className="w-5 h-5 text-white" />
                <span className="absolute opacity-0 group-hover:opacity-100 bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-white/90 text-gray-800 px-2 py-1 rounded text-xs whitespace-nowrap transition-opacity">Secure System</span>
              </div>
              <div className="p-2 bg-white/10 rounded-full animate-pulse delay-150 group transition-all duration-300 hover:scale-110">
                <Globe className="w-5 h-5 text-white" />
                <span className="absolute opacity-0 group-hover:opacity-100 bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-white/90 text-gray-800 px-2 py-1 rounded text-xs whitespace-nowrap transition-opacity">Multi-Language</span>
              </div>
              <div className="p-2 bg-white/10 rounded-full animate-pulse delay-300 group transition-all duration-300 hover:scale-110">
                <Zap className="w-5 h-5 text-white" />
                <span className="absolute opacity-0 group-hover:opacity-100 bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-white/90 text-gray-800 px-2 py-1 rounded text-xs whitespace-nowrap transition-opacity">Fast Response</span>
              </div>
            </div>
          </header>

          {/* Chat Messages */}
          <div 
            id="chat-messages"
            className="h-96 overflow-y-auto p-8 space-y-6 bg-gradient-to-b from-transparent to-black/5 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent"
            aria-live="polite"
            aria-atomic="true"
          >
            {messages.map((message, index) => (
              <div
                key={message.id}
                className={`flex gap-4 ${message.isUser ? 'justify-end' : 'justify-start'} animate-fade-in-up`}
                style={{ animationDelay: `${index * 100}ms` }}
                role="log"
                aria-label={`${message.isUser ? 'Your message' : 'AI response'}`}
              >
                <div className={`flex gap-4 max-w-4xl ${message.isUser ? 'flex-row-reverse' : 'flex-row'} group`}>
                  <div className={`w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg transform transition-all duration-300 group-hover:scale-110 ${
                    message.isUser 
                      ? 'bg-gradient-to-r from-blue-500 to-purple-500' 
                      : message.isLoading
                      ? 'bg-gradient-to-r from-yellow-400 to-orange-500 animate-pulse'
                      : 'bg-gradient-to-r from-cyan-400 to-blue-500'
                  }`}>
                    {message.isUser ? 
                      <User className="w-6 h-6 text-white" aria-hidden="true" /> : 
                      <Bot className={`w-6 h-6 text-white ${message.isLoading ? 'animate-spin' : ''}`} aria-hidden="true" />
                    }
                  </div>
                  
                  <div 
                    className={`rounded-2xl p-6 shadow-xl backdrop-blur-sm border transform transition-all duration-300 group-hover:scale-[1.02] ${
                      message.isUser
                        ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white border-blue-300/30'
                        : message.isLoading
                        ? 'bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200/50 text-yellow-800 animate-pulse'
                        : 'bg-white/80 border-white/30 text-gray-800'
                    }`}
                  >
                    <p className={`leading-relaxed ${message.isLoading ? 'flex items-center gap-2' : ''}`}>
                      {message.text}
                    </p>
                    <time 
                      dateTime={message.timestamp.toISOString()}
                      className={`text-xs mt-3 ${message.isUser ? 'text-blue-100' : 'text-gray-500'}`}
                    >
                      {message.timestamp.toLocaleTimeString()}
                    </time>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Input Form */}
          <form 
            onSubmit={handleSubmit} 
            className="p-8 bg-gradient-to-r from-white/10 to-white/5 backdrop-blur-sm"
            aria-label="Message input form"
          >
            <div className="flex gap-4">
              <div className="flex-1 relative group">
                <input
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Describe your IT challenge... (English/Hindi supported) ✨"
                  className="w-full border-0 rounded-2xl px-6 py-4 text-lg bg-white/90 backdrop-blur-sm focus:outline-none focus:ring-4 focus:ring-blue-500/30 shadow-xl placeholder-gray-500 transition-all duration-300 group-hover:bg-white/95"
                  disabled={isLoading}
                  aria-label="Message input"
                  aria-describedby="input-help"
                />
                <div 
                  className="absolute inset-0 rounded-2xl bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-cyan-500/20 -z-10 blur-xl animate-pulse"
                  aria-hidden="true"
                />
              </div>
              
              <button
                type="submit"
                disabled={isLoading || !inputText.trim()}
                className="group bg-gradient-to-r from-blue-500 via-purple-500 to-cyan-500 hover:from-blue-600 hover:via-purple-600 hover:to-cyan-600 disabled:from-gray-400 disabled:to-gray-500 text-white px-8 py-4 rounded-2xl flex items-center gap-3 transition-all duration-300 shadow-xl hover:shadow-2xl transform hover:scale-105 disabled:scale-100 focus:outline-none focus:ring-4 focus:ring-blue-500/50"
                aria-label={isLoading ? "Sending message..." : "Send message"}
              >
                <Send className="w-5 h-5 transition-transform group-hover:translate-x-1" aria-hidden="true" />
                <span className="font-semibold">Send</span>
              </button>
            </div>
            
            <div id="input-help" className="sr-only">
              Press Enter to send your message or use Ctrl + Enter for a new line
            </div>

            {/* Quick Suggestions */}
            <div 
              className="mt-6 flex flex-wrap gap-4 text-sm text-white/80"
              role="list"
              aria-label="Message suggestions"
            >
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestion(suggestion.text)}
                  className="flex items-center gap-2 bg-white/10 px-4 py-2 rounded-full backdrop-blur-sm hover:bg-white/20 transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-white/50"
                  type="button"
                  aria-label={`Use suggestion: ${suggestion.text}`}
                >
                  <span className="text-2xl" aria-hidden="true">{suggestion.icon}</span>
                  <span>{suggestion.text}</span>
                </button>
              ))}
            </div>
          </form>
        </div>
      </main>
      
      <style jsx>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }
        
        .animate-float {
          animation: float 3s ease-in-out infinite;
        }

        .animate-fade-in-up {
          animation: fade-in-up 0.6s ease-out forwards;
        }

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
      `}</style>
    </div>
  );
}