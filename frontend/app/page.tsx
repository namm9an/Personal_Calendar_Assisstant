import Link from "next/link";
import { motion } from "framer-motion";

const MotionH1 = motion.h1;
const MotionP = motion.p;
const MotionDiv = motion.div;

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 md:p-24 relative overflow-hidden">
      {/* Hero Section */}
      <div className="w-full max-w-6xl mx-auto relative z-10">
        <div className="text-center space-y-8 mb-16">
          {/* Main Heading with Gradient */}
          <MotionH1 
            className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <span className="block">Your AI Calendar</span>
            <span className="bg-gradient-to-r from-primary via-accent to-secondary bg-clip-text text-transparent animate-gradient-shift spaced-text">
              Reimagined
            </span>
          </MotionH1>
          
          {/* Subheading */}
          <MotionP 
            className="text-xl md:text-2xl text-white/80 max-w-2xl mx-auto conversational-text"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.8 }}
          >
            Organize your schedule effortlessly with our AI-powered calendar assistant that adapts to your needs.
          </MotionP>
          
          {/* CTA Buttons */}
          <MotionDiv 
            className="flex flex-col sm:flex-row gap-4 justify-center mt-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.8 }}
          >
            <Link 
              href="/signup" 
              className="px-8 py-4 rounded-md bg-gradient-to-r from-primary to-accent text-white font-bold text-lg shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 hover:scale-105 transition-all duration-300 relative overflow-hidden group"
            >
              <span className="relative z-10">Get Started</span>
              <span className="absolute inset-0 w-full h-full bg-white/20 animate-shine"></span>
            </Link>
            
            <Link 
              href="/login" 
              className="px-8 py-4 rounded-md border border-white/20 bg-black/50 backdrop-blur-md text-white font-bold text-lg hover:bg-white/10 transition-all duration-300"
            >
              Log In
            </Link>
          </MotionDiv>
        </div>
        
        {/* Features Section */}
        <MotionDiv 
          className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7, duration: 0.8 }}
        >
          {/* Feature 1 */}
          <div className="glass-card p-6 rounded-xl border border-white/20 relative overflow-hidden group">
            <div className="absolute -top-24 -right-24 w-40 h-40 bg-primary/20 rounded-full blur-3xl group-hover:bg-primary/30 transition-all duration-700"></div>
            <h3 className="text-xl font-bold mb-3 text-white relative z-10">Smart Scheduling</h3>
            <p className="text-white/70 relative z-10">AI-powered scheduling that learns your preferences and optimizes your calendar.</p>
          </div>
          
          {/* Feature 2 */}
          <div className="glass-card p-6 rounded-xl border border-white/20 relative overflow-hidden group">
            <div className="absolute -top-24 -right-24 w-40 h-40 bg-accent/20 rounded-full blur-3xl group-hover:bg-accent/30 transition-all duration-700"></div>
            <h3 className="text-xl font-bold mb-3 text-white relative z-10">Voice Commands</h3>
            <p className="text-white/70 relative z-10">Create and manage events using natural language voice commands.</p>
          </div>
          
          {/* Feature 3 */}
          <div className="glass-card p-6 rounded-xl border border-white/20 relative overflow-hidden group">
            <div className="absolute -top-24 -right-24 w-40 h-40 bg-secondary/20 rounded-full blur-3xl group-hover:bg-secondary/30 transition-all duration-700"></div>
            <h3 className="text-xl font-bold mb-3 text-white relative z-10">Smart Reminders</h3>
            <p className="text-white/70 relative z-10">Contextual reminders that know when and how to notify you.</p>
          </div>
        </MotionDiv>
      </div>
      
      {/* Scroll Indicator */}
      <MotionDiv 
        className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1, y: [0, 10, 0] }}
        transition={{ 
          opacity: { delay: 1.5, duration: 1 },
          y: { delay: 1.5, duration: 1.5, repeat: Infinity, ease: "easeInOut" }
        }}
      >
        <div className="w-6 h-10 rounded-full border-2 border-white/30 flex justify-center pt-2">
          <MotionDiv 
            className="w-1 h-2 bg-white/60 rounded-full"
            animate={{ y: [0, 4, 0] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          />
        </div>
      </MotionDiv>
      
      {/* Decorative border elements */}
      <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent"></div>
      <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent"></div>
    </main>
  );
}
