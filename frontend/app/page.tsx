"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import dynamic from 'next/dynamic';
import { motion } from 'framer-motion';

const features = [
  {
    title: "AI-Powered Scheduling",
    description: "Our assistant learns your preferences to find the perfect meeting times.",
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    title: "Natural Language Processing",
    description: "Just type or speak naturally to schedule, reschedule, or cancel meetings.",
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
      </svg>
    ),
  },
  {
    title: "Cross-Platform Sync",
    description: "Seamlessly sync with Google Calendar, Outlook, and Apple Calendar.",
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
      </svg>
    ),
  },
];

const Dashboard = dynamic(() => import('@/components/dashboard/Dashboard'), {
  loading: () => <div>Loading...</div>,
  ssr: false
});

export default function Home() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Content */}
      <div className="relative z-10 text-center max-w-5xl mx-auto px-4">
        <motion.h1 
          className="text-6xl md:text-7xl lg:text-8xl font-bold mb-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          Your AI Calendar
          <br />
          <span className="text-gradient-brand text-6xl md:text-7xl lg:text-8xl">Reimagined</span>
        </motion.h1>
        
        <motion.p 
          className="text-xl lg:text-2xl text-neutral-300 mb-8 max-w-3xl mx-auto"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.8 }}
        >
          Experience the future of scheduling with our intelligent assistant that learns your preferences and manages your time effortlessly.
        </motion.p>
        
        {/* Feature Cards */}
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.8 }}
        >
          {features.map((feature, index) => (
            <motion.div 
              key={index}
              className="glass-card p-6 flex flex-col items-center text-center"
              whileHover={{ y: -5, boxShadow: "0 10px 30px -10px rgba(6, 182, 212, 0.2)" }}
              transition={{ duration: 0.2 }}
            >
              <div className="w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center mb-4 text-accent">
                {feature.icon}
              </div>
              <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
              <p className="text-neutral-400">{feature.description}</p>
            </motion.div>
          ))}
        </motion.div>
        
        {/* CTA Buttons */}
        <motion.div 
          className="flex flex-col sm:flex-row gap-4 justify-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.8 }}
        >
          <Link href="/signup">
            <Button className="group relative px-8 py-6 bg-gradient-to-r from-accent to-primary text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 animate-shine">
              <span className="relative z-10 text-lg">Start Free Trial</span>
            </Button>
          </Link>
          <Link href="/login">
            <Button variant="outline" className="group relative px-8 py-6 border border-white/20 bg-white/5 backdrop-blur-sm text-white font-semibold rounded-xl hover:bg-white/10 transform hover:scale-105 transition-all duration-300">
              <span className="relative z-10 text-lg">Log In</span>
            </Button>
          </Link>
        </motion.div>
      </div>
      
      {/* Scroll Indicator */}
      <motion.div 
        className="absolute bottom-10 left-1/2 transform -translate-x-1/2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 0.8 }}
      >
        <motion.div 
          className="w-6 h-10 border-2 border-white/30 rounded-full flex justify-center"
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
        >
          <div className="w-1 h-3 bg-white/50 rounded-full mt-2"></div>
        </motion.div>
      </motion.div>
    </section>
  );
}
