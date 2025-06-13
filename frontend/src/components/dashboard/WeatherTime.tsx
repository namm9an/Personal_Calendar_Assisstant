import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const WeatherTime = () => {
  const [time, setTime] = useState(new Date());
  const [weather, setWeather] = useState({ temp: 22, condition: 'Sunny' });

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <motion.div 
      className="weather-time bg-white/10 backdrop-blur-lg rounded-2xl p-4"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
    >
      <div className="flex items-center justify-between">
        <div>
          <div className="text-2xl font-bold">
            {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
          <div className="text-sm">
            {time.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' })}
          </div>
        </div>
        <div className="text-right">
          <div className="text-xl">{weather.temp}°C</div>
          <div className="text-sm">{weather.condition}</div>
        </div>
      </div>
    </motion.div>
  );
};

export default WeatherTime;
