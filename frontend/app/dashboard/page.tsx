"use client";

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { motion } from 'framer-motion';
import CalendarView from '@/components/CalendarView';
import AgentChat from '@/components/AgentChat';

// A reusable card component for the dashboard widgets
const DashboardCard = ({ title, children, className }: { title: string, children: React.ReactNode, className?: string }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, type: 'spring' }}
    className={`bg-black/20 backdrop-blur-lg border border-white/10 rounded-2xl p-6 shadow-lg hover:border-white/20 transition-all duration-300 ${className}`}
  >
    <h3 className="text-xl font-bold text-white mb-4">{title}</h3>
    <div>{children}</div>
  </motion.div>
);


export default function DashboardPage() {
  const [user, setUser] = useState<{ email: string; fullName: string } | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/users/me`, {
          credentials: 'include',
        });
        if (res.ok) {
          const data = await res.json();
          setUser({ email: data.email, fullName: data.full_name });
        } else {
          window.location.href = '/login';
        }
      } catch (error) {
        console.error('Failed to fetch user', error);
        window.location.href = '/login';
      } finally {
        setIsLoading(false);
      }
    };

    fetchUser();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-transparent">
        <div className="w-16 h-16 border-4 border-dashed rounded-full animate-spin border-primary"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <DashboardLayout>
      <div className="text-white h-full flex flex-col gap-8">
        <motion.h1
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-b from-white to-neutral-300 flex-shrink-0"
        >
          Welcome back, {user.fullName}
        </motion.h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-1">
          <div className="lg:col-span-2 h-[600px]">
            <CalendarView />
          </div>
          <div className="flex flex-col gap-8">
            <DashboardCard title="Quick Actions">
              <div className="flex flex-col gap-2 text-neutral-200">
                <button className="text-left p-2 rounded-md hover:bg-white/10 transition-colors">Create New Event</button>
                <button className="text-left p-2 rounded-md hover:bg-white/10 transition-colors">Start Chat with AI</button>
              </div>
            </DashboardCard>
            <DashboardCard title="Recent Activity">
              <p className="text-neutral-300">AI scheduled "Project Sync" for tomorrow.</p>
              {/* Activity feed will go here */}
            </DashboardCard>
          </div>
        </div>
      </div>
      <AgentChat />
    </DashboardLayout>
  );
}
