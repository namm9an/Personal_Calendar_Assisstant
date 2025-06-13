"use client";

import { useAuth } from "../src/context/AuthContext";
import AuthForm from "../src/components/AuthForm";
import CalendarView from "../src/components/CalendarView";
import AgentChat from "../src/components/AgentChat";
import Navbar from "../src/components/Navbar";

export default function Home() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>Loading...</p>
      </div>
    );
  }

  if (!user) {
    return <AuthForm />;
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <Navbar />
      <main className="flex flex-1 overflow-hidden p-4 gap-4">
        <div className="w-2/3 h-full overflow-y-auto bg-white rounded-lg shadow-md p-4">
          <CalendarView />
        </div>
        <div className="w-1/3 h-full flex flex-col bg-white rounded-lg shadow-md">
          <AgentChat />
        </div>
      </main>
    </div>
  );
}
