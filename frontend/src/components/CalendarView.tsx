"use client";

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval, addMonths, subMonths, isSameMonth, isSameDay } from 'date-fns';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface CalendarEvent {
  id: string;
  summary: string;
  start: { dateTime: string };
  end: { dateTime: string };
}

const CalendarView = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchEvents = async () => {
      setIsLoading(true);
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/events/`,
          {
            credentials: 'include',
          }
        );
        if (res.ok) {
          const data = await res.json();
          setEvents(data.events || []);
        } else {
          console.error('Failed to fetch events');
          setEvents([]);
        }
      } catch (error) {
        console.error('Error fetching events:', error);
        setEvents([]);
      } finally {
        setIsLoading(false);
      }
    };
    fetchEvents();
  }, [currentDate]);

  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(monthStart);
  const startDate = startOfWeek(monthStart);
  const endDate = endOfWeek(monthEnd);
  const days = eachDayOfInterval({ start: startDate, end: endDate });

  const nextMonth = () => setCurrentDate(addMonths(currentDate, 1));
  const prevMonth = () => setCurrentDate(subMonths(currentDate, 1));

  const getEventsForDay = (day: Date) => {
    return events.filter(event => isSameDay(new Date(event.start.dateTime), day));
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-black/20 backdrop-blur-lg border border-white/10 rounded-2xl p-6 shadow-lg h-full flex flex-col"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-white">{format(currentDate, 'MMMM yyyy')}</h2>
        <div className="flex items-center gap-2">
          <button onClick={prevMonth} className="p-2 rounded-full hover:bg-white/10 transition-colors text-neutral-300">
            <ChevronLeft size={20} />
          </button>
          <button onClick={nextMonth} className="p-2 rounded-full hover:bg-white/10 transition-colors text-neutral-300">
            <ChevronRight size={20} />
          </button>
        </div>
      </div>

      {/* Days of the week */}
      <div className="grid grid-cols-7 gap-2 text-center text-xs font-semibold text-neutral-400 mb-2">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => <div key={day}>{day}</div>)}
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7 grid-rows-5 gap-2 flex-1">
        {days.map(day => (
          <div
            key={day.toString()}
            className={`border border-white/10 rounded-lg p-2 flex flex-col transition-colors ${
              isSameMonth(day, currentDate) ? 'bg-white/5' : 'bg-transparent text-neutral-500'
            } ${isSameDay(day, new Date()) ? 'border-primary' : ''}`}
          >
            <span className={`font-semibold text-sm ${isSameDay(day, new Date()) ? 'text-primary' : ''}`}>
              {format(day, 'd')}
            </span>
            <div className="mt-1 space-y-1 overflow-y-auto">
              {getEventsForDay(day).map(event => (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="bg-accent/50 text-white text-xs p-1 rounded-md truncate cursor-pointer hover:bg-accent"
                >
                  {event.summary}
                </motion.div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
};

export default CalendarView;