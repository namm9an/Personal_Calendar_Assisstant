'use client';

import React from 'react';
import QuickActions from './QuickActions';
import ActivityFeed from './ActivityFeed';
import WeatherTime from './WeatherTime';
import { MagneticButton } from "../ui/MagneticButton";
import { ShimmerLoader } from "../ui/ShimmerLoader";
import { AnimatedBackground } from '../ui/AnimatedBackground';

const Dashboard = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-800 p-4 relative overflow-hidden">
      <AnimatedBackground />
      
      <div className="dashboard grid grid-cols-4 gap-4 max-w-7xl mx-auto relative z-10">
        {/* Sidebar */}
        <div 
          className="col-span-1 bg-white/10 backdrop-blur-lg rounded-2xl p-4"
        >
          <h2 className="text-xl font-bold mb-4">Navigation</h2>
          {/* Navigation items */}
        </div>

        {/* Main content */}
        <div 
          className="col-span-2 bg-white/10 backdrop-blur-lg rounded-2xl p-4"
        >
          <h2 className="text-xl font-bold mb-4">Calendar Overview</h2>
          {/* Calendar content */}
        </div>

        {/* Right column */}
        <div className="col-span-1 flex flex-col gap-4">
          <WeatherTime />
          <div className="quick-actions-container bg-white/10 backdrop-blur-lg rounded-2xl p-4">
            <QuickActions />
          </div>
          <div className="activity-feed-container bg-white/10 backdrop-blur-lg rounded-2xl p-4">
            <ActivityFeed />
          </div>
        </div>
      </div>

      {/* Parallax floating elements */}
      <div
        className="absolute bottom-10 right-10 w-24 h-24 bg-pink-500/20 rounded-full blur-xl"
      />
      <div
        className="absolute top-20 left-1/4 w-16 h-16 bg-purple-500/20 rounded-full blur-xl"
      />
    </div>
  );
};

export default Dashboard;
