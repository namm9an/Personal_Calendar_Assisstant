import React from 'react';
import { motion } from 'framer-motion';

const ActivityFeed = () => {
  const activities = [
    { id: 1, action: 'Meeting scheduled', time: '10:30 AM', details: 'Team sync' },
    { id: 2, action: 'Document shared', time: '9:15 AM', details: 'Project proposal.pdf' },
    { id: 3, action: 'Reminder set', time: '8:00 AM', details: 'Call with client' },
  ];

  return (
    <motion.div 
      className="activity-feed"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
    >
      <h3 className="text-lg font-semibold mb-2">Activity Feed</h3>
      <div className="space-y-3">
        {activities.map((activity, index) => (
          <motion.div
            key={activity.id}
            className="bg-white/5 rounded-xl p-3"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 + index * 0.1 }}
          >
            <div className="flex justify-between">
              <span className="font-medium">{activity.action}</span>
              <span className="text-sm text-gray-400">{activity.time}</span>
            </div>
            <p className="text-sm mt-1">{activity.details}</p>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

export default ActivityFeed;
