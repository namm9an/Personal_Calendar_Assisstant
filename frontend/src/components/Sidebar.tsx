"use client";

import { useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { LayoutGrid, Calendar, MessageSquare, Settings, ChevronLeft, ChevronRight } from 'lucide-react';
import { usePathname } from 'next/navigation';

const navItems = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutGrid },
  { name: 'Calendar', href: '/dashboard/calendar', icon: Calendar },
  { name: 'Chat', href: '/dashboard/chat', icon: MessageSquare },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export default function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const pathname = usePathname();

  const sidebarVariants = {
    collapsed: { width: '80px' },
    expanded: { width: '250px' },
  };

  return (
    <motion.aside
      variants={sidebarVariants}
      initial={false}
      animate={isCollapsed ? 'collapsed' : 'expanded'}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="h-screen p-4 bg-black/20 backdrop-blur-lg border-r border-white/10 flex flex-col justify-between relative"
    >
      <div>
        <div className="flex items-center justify-center mb-10 h-8">
          <AnimatePresence>
          {!isCollapsed && (
            <motion.div initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}} transition={{duration: 0.2}}>
              <Link href="/" className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary">
                CalendarAI
              </Link>
            </motion.div>
          )}
          </AnimatePresence>
        </div>
        <nav className="flex flex-col gap-2">
          {navItems.map((item) => (
            <Link href={item.href} key={item.name} title={item.name}>
              <div
                className={`flex items-center gap-4 p-3 rounded-lg transition-colors cursor-pointer ${
                  pathname === item.href
                    ? 'bg-primary/80 text-white shadow-lg shadow-primary/50'
                    : 'text-neutral-300 hover:bg-white/10'
                } ${isCollapsed ? 'justify-center' : ''}`}
              >
                <item.icon className="h-6 w-6 flex-shrink-0" />
                <AnimatePresence>
                  {!isCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      transition={{ duration: 0.2, delay: 0.1 }}
                      className="font-semibold whitespace-nowrap"
                    >
                      {item.name}
                    </motion.span>
                  )}
                </AnimatePresence>
              </div>
            </Link>
          ))}
        </nav>
      </div>
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute -right-4 top-1/2 -translate-y-1/2 p-1 rounded-full bg-primary/80 hover:bg-primary transition-transform hover:scale-110 border-2 border-background"
      >
        {isCollapsed ? <ChevronRight className="h-5 w-5 text-white" /> : <ChevronLeft className="h-5 w-5 text-white" />}
      </button>
    </motion.aside>
  );
}
