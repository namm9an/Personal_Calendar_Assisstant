"use client";

import Link from 'next/link';
import { motion } from 'framer-motion';

export default function Header() {
  return (
    <motion.header
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: 'spring', stiffness: 100, damping: 20 }}
      className="fixed top-4 left-1/2 -translate-x-1/2 w-[95%] max-w-5xl z-50"
    >
      <nav className="flex items-center justify-between p-4 rounded-2xl bg-black/20 backdrop-blur-lg border border-white/10 shadow-lg">
        <Link href="/" className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary">
          CalendarAI
        </Link>
        <div className="flex items-center gap-6 text-lg text-neutral-200">
          <Link href="#features" className="hover:text-white transition-colors">Features</Link>
          <Link href="/login" className="hover:text-white transition-colors">Login</Link>
          <Link href="/signup">
            <button className="px-5 py-2 font-semibold text-white bg-gradient-to-r from-primary to-secondary rounded-full transition-all duration-300 ease-out hover:scale-105">
              Sign Up
            </button>
          </Link>
        </div>
      </nav>
    </motion.header>
  );
}
