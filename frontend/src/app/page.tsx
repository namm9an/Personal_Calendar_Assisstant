"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import Navbar from "@/components/Navbar";

export default function HomePage() {
  const { user, loading } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar user={user} />
      
      <main className="flex-1 flex flex-col items-center justify-center px-4">
        <div className="text-center max-w-3xl mx-auto">
          <h1 className="text-4xl font-bold text-gray-900 sm:text-5xl">
            Personal Calendar Assistant
          </h1>
          <p className="mt-6 text-xl text-gray-600">
            AI-powered calendar management to help you schedule, reschedule, and manage your events efficiently.
          </p>
          <div className="mt-10">
            {loading ? (
              <div className="animate-spin h-8 w-8 border-4 border-blue-500 rounded-full border-t-transparent mx-auto"></div>
            ) : user ? (
              <Link
                href="/dashboard"
                className="px-8 py-3 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Go to Dashboard
              </Link>
            ) : (
              <div className="space-x-4">
                <Link
                  href="/login"
                  className="px-8 py-3 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  Login
                </Link>
                <Link
                  href="/signup"
                  className="px-8 py-3 bg-gray-200 text-gray-900 rounded-md font-medium hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2"
                >
                  Sign Up
                </Link>
              </div>
            )}
          </div>
          
          <div className="mt-16 border-t border-gray-200 pt-8">
            <h2 className="text-2xl font-bold text-gray-900">Features</h2>
            <div className="mt-6 grid grid-cols-1 gap-8 md:grid-cols-3">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-gray-900">Smart Scheduling</h3>
                <p className="mt-2 text-gray-600">
                  Ask your assistant to find free slots or create new meetings with natural language.
                </p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-gray-900">Integration</h3>
                <p className="mt-2 text-gray-600">
                  Works with Google Calendar and Microsoft Calendar for seamless event management.
                </p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-gray-900">AI-Powered</h3>
                <p className="mt-2 text-gray-600">
                  Powered by advanced AI to understand your scheduling needs and preferences.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
      
      <footer className="bg-white py-4 border-t">
        <div className="container mx-auto px-4 text-center text-sm text-gray-600">
          <p>© {new Date().getFullYear()} Personal Calendar Assistant</p>
        </div>
      </footer>
    </div>
  );
} 