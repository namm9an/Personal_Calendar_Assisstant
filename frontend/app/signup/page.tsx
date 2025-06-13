"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function SignupPage() {
  return (
    <div className="min-h-screen flex">
      {/* Left Side - Animated Background */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600">
          {/* Animated Geometric Shapes */}
          <div className="absolute inset-0">
            <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-white/20 rounded-full animate-float"></div>
            <div className="absolute top-3/4 right-1/4 w-24 h-24 bg-white/30 rounded-lg rotate-45 animate-float-delayed"></div>
            <div className="absolute bottom-1/4 left-1/3 w-40 h-40 bg-white/10 rounded-full animate-pulse"></div>
          </div>
        </div>
        
        {/* Content Overlay */}
        <div className="relative z-10 flex flex-col justify-center p-12 text-white">
          <h2 className="text-4xl font-bold mb-4">Create Your Account</h2>
          <p className="text-xl opacity-90">Join the future of scheduling</p>
        </div>
      </div>
      
      {/* Right Side - Signup Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-gray-50">
        <div className="w-full max-w-md">
          {/* Glass Card */}
          <div className="bg-white/70 backdrop-blur-xl rounded-3xl p-8 shadow-2xl border border-white/20">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Sign Up</h1>
              <p className="text-gray-600">Create your account to get started</p>
            </div>
            
            <form className="space-y-6">
              {/* Name Input */}
              <div className="relative">
                <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
                <input 
                  type="text" 
                  className="w-full px-4 py-4 bg-white/50 border border-gray-200 rounded-2xl focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:bg-white transition-all duration-300 placeholder-gray-400"
                  placeholder="John Doe"
                />
              </div>
              
              {/* Email Input */}
              <div className="relative">
                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                <input 
                  type="email" 
                  className="w-full px-4 py-4 bg-white/50 border border-gray-200 rounded-2xl focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:bg-white transition-all duration-300 placeholder-gray-400"
                  placeholder="you@example.com"
                />
              </div>
              
              {/* Password Input */}
              <div className="relative">
                <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
                <input 
                  type="password" 
                  className="w-full px-4 py-4 bg-white/50 border border-gray-200 rounded-2xl focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:bg-white transition-all duration-300 placeholder-gray-400"
                  placeholder="••••••••"
                />
              </div>
              
              {/* Confirm Password Input */}
              <div className="relative">
                <label className="block text-sm font-medium text-gray-700 mb-2">Confirm Password</label>
                <input 
                  type="password" 
                  className="w-full px-4 py-4 bg-white/50 border border-gray-200 rounded-2xl focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:bg-white transition-all duration-300 placeholder-gray-400"
                  placeholder="••••••••"
                />
              </div>
              
              {/* Sign Up Button */}
              <Button className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold rounded-2xl hover:from-indigo-700 hover:to-purple-700 transform hover:scale-[1.02] transition-all duration-300 shadow-lg hover:shadow-xl">
                Sign Up
              </Button>
            </form>
            
            {/* Social Login */}
            <div className="mt-8 pt-8 border-t border-gray-200">
              <p className="text-center text-gray-600 mb-4">Or sign up with</p>
              <div className="grid grid-cols-2 gap-4">
                <Button className="flex items-center justify-center px-4 py-3 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors duration-200">
                  {/* GoogleIcon should be imported or defined */}
                  <span className="mr-2">G</span>
                  Google
                </Button>
                <Button className="flex items-center justify-center px-4 py-3 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors duration-200">
                  {/* MicrosoftIcon should be imported or defined */}
                  <span className="mr-2">M</span>
                  Microsoft
                </Button>
              </div>
            </div>
            
            <p className="text-center text-gray-600 mt-6">
              Already have an account? 
              <Link href="/login" className="text-indigo-600 hover:text-indigo-700 font-medium ml-1">Log in</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
