import Link from "next/link";
import { motion } from "framer-motion";
import { AuthForm } from "@/components/AuthForm";

const MotionDiv = motion.div;
const MotionH1 = motion.h1;
const MotionP = motion.p;

export default function LoginPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 md:p-24 relative overflow-hidden">
      <div className="w-full max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
        {/* Left column - Hidden on mobile, visible on larger screens */}
        <MotionDiv 
          className="hidden lg:flex flex-col items-center justify-center relative"
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <div className="relative">
            {/* Background elements */}
            <div className="absolute -z-10 inset-0 blur-3xl bg-gradient-to-br from-primary/20 via-accent/20 to-secondary/20 rounded-full transform -translate-x-1/4 -translate-y-1/4 w-[150%] h-[150%]"></div>
            
            {/* Content */}
            <div className="text-center space-y-6 p-8">
              <MotionH1 
                className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-primary via-accent to-secondary bg-clip-text text-transparent"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3, duration: 0.8 }}
              >
                Welcome Back
              </MotionH1>
              
              <MotionP 
                className="text-xl text-white/80 max-w-md conversational-text"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5, duration: 0.8 }}
              >
                Your personal calendar assistant is ready to help you organize your schedule and boost your productivity.
              </MotionP>
              
              {/* Decorative elements */}
              <MotionDiv 
                className="w-16 h-16 border border-accent/30 rounded-lg absolute -bottom-8 -left-8 -z-10"
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              />
              
              <MotionDiv 
                className="w-24 h-24 border border-primary/30 rounded-full absolute -top-12 -right-12 -z-10"
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
              />
            </div>
          </div>
        </MotionDiv>
        
        {/* Right column - Auth form */}
        <div className="w-full">
          <AuthForm mode="login" />
        </div>
      </div>
    </main>
  );
}
