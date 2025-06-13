'use client';

import React from 'react';

const ActivityFeed = () => {
  const activities = [
    { id: 1, action: 'Meeting scheduled', time: '10:30 AM', details: 'Team sync' },
    { id: 2, action: 'Document shared', time: '9:15 AM', details: 'Project proposal.pdf' },
    { id: 3, action: 'Reminder set', time: '8:00 AM', details: 'Call with client' },
  ];

  return (
    <div className="activity-feed">
      <h3 className="text-lg font-semibold mb-2">Activity Feed</h3>
      <div className="space-y-3">
        {activities.map((activity) => (
          <div
            key={activity.id}
            className="bg-white/5 rounded-xl p-3"
          >
            <div className="flex justify-between">
              <span className="font-medium">{activity.action}</span>
              <span className="text-sm text-gray-400">{activity.time}</span>
            </div>
            <p className="text-sm mt-1">{activity.details}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ActivityFeed;
