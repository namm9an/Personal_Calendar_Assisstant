"use client";

import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const MotionDiv = motion.div;

export const AnimatedBackground = () => {
  const [mounted, setMounted] = useState(false);
  
  useEffect(() => {
    setMounted(true);
  }, []);
  
  if (!mounted) return null;
  
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none bg-black">
      {/* Subtle grid pattern */}
      <div className="absolute inset-0 opacity-10">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="0.5"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      {/* Digital circuit lines */}
      <div className="absolute inset-0 circuit-pattern opacity-10"></div>
      
      {/* Larger, slower moving background elements */}
      {[...Array(5)].map((_, i) => (
        <MotionDiv
          key={`large-${i}`}
          className="absolute rounded-full bg-gradient-to-br from-primary/20 to-accent/20 blur-3xl"
          style={{
            width: `${Math.random() * 300 + 200}px`,
            height: `${Math.random() * 300 + 200}px`,
            top: `${Math.random() * 100}%`,
            left: `${Math.random() * 100}%`,
          }}
          animate={{
            x: [0, (Math.random() - 0.5) * 50],
            y: [0, (Math.random() - 0.5) * 50],
          }}
          transition={{
            duration: 30 + Math.random() * 20,
            repeat: Infinity,
            repeatType: "reverse",
            ease: "easeInOut"
          }}
        />
      ))}
      
      {/* Medium sized elements with moderate movement */}
      {[...Array(8)].map((_, i) => (
        <MotionDiv
          key={`medium-${i}`}
          className="absolute rounded-full bg-gradient-to-br from-secondary/20 to-primary/20 blur-xl"
          style={{
            width: `${Math.random() * 150 + 100}px`,
            height: `${Math.random() * 150 + 100}px`,
            top: `${Math.random() * 100}%`,
            left: `${Math.random() * 100}%`,
          }}
          animate={{
            x: [0, (Math.random() - 0.5) * 100],
            y: [0, (Math.random() - 0.5) * 100],
            rotate: [0, 360],
          }}
          transition={{
            duration: 20 + Math.random() * 15,
            repeat: Infinity,
            repeatType: "reverse",
            ease: "easeInOut"
          }}
        />
      ))}
      
      {/* Smaller, faster moving elements */}
      {[...Array(10)].map((_, i) => (
        <MotionDiv
          key={`small-${i}`}
          className="absolute rounded-full bg-gradient-to-br from-accent/25 to-secondary/25 blur-lg"
          style={{
            width: `${Math.random() * 60 + 40}px`,
            height: `${Math.random() * 60 + 40}px`,
            top: `${Math.random() * 100}%`,
            left: `${Math.random() * 100}%`,
          }}
          animate={{
            x: [0, (Math.random() - 0.5) * 150],
            y: [0, (Math.random() - 0.5) * 150],
            rotate: [0, Math.random() > 0.5 ? 360 : -360],
          }}
          transition={{
            duration: 15 + Math.random() * 10,
            repeat: Infinity,
            repeatType: "reverse",
            ease: "easeInOut"
          }}
        />
      ))}
      
      {/* Scattered small dots */}
      {[...Array(40)].map((_, i) => (
        <MotionDiv
          key={`dot-${i}`}
          className="absolute rounded-full bg-white"
          style={{
            width: `${Math.random() * 3 + 1}px`,
            height: `${Math.random() * 3 + 1}px`,
            top: `${Math.random() * 100}%`,
            left: `${Math.random() * 100}%`,
            opacity: Math.random() * 0.5 + 0.3,
          }}
          animate={{
            opacity: [0.3, 0.7, 0.3],
            scale: [1, 1.5, 1],
          }}
          transition={{
            duration: 3 + Math.random() * 2,
            repeat: Infinity,
            ease: "easeInOut",
            delay: Math.random() * 2,
          }}
        />
      ))}
      
      {/* Cyber elements */}
      <div className="absolute top-20 right-20 w-40 h-40 border border-accent/30 rounded-lg rotate-12 opacity-30" />
      <div className="absolute bottom-40 left-20 w-60 h-20 border border-primary/30 rounded-lg -rotate-6 opacity-30" />
      
      {/* Asymmetrical geometric shapes */}
      <MotionDiv
        className="absolute w-64 h-64 border border-white/10 rounded-lg"
        style={{
          top: '15%',
          left: '10%',
          transform: 'rotate(15deg)',
        }}
        animate={{
          rotate: [15, 25, 15],
          scale: [1, 1.05, 1],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      
      <MotionDiv
        className="absolute w-40 h-40 border border-white/10 rounded-full"
        style={{
          bottom: '20%',
          right: '15%',
        }}
        animate={{
          scale: [1, 1.2, 1],
          rotate: [0, -15, 0],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />

      {/* Futuristic scan line */}
      <MotionDiv 
        className="absolute inset-0 scan-line opacity-10"
        animate={{
          top: ["-100%", "200%"],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "linear",
        }}
      />
    </div>
  );
};

export default AnimatedBackground;
