import { useState, useEffect } from "react";
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval, addMonths, subMonths, isSameMonth, isSameDay, parseISO } from 'date-fns';

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
    fetchEvents();
  }, [currentDate]);

  const fetchEvents = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/events`, {
        method: "GET",
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error("Failed to fetch events");
      }
      const data = await response.json();
      setEvents(data.events || []);
    } catch (error) {
      console.error("Error fetching events:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(monthStart);
  const startDate = startOfWeek(monthStart);
  const endDate = endOfWeek(monthEnd);
  const days = eachDayOfInterval({ start: startDate, end: endDate });

  const nextMonth = () => setCurrentDate(addMonths(currentDate, 1));
  const prevMonth = () => setCurrentDate(subMonths(currentDate, 1));

  const getEventsForDay = (day: Date) => {
    return events.filter(event => {
      const eventDate = parseISO(event.start.dateTime);
      return isSameDay(eventDate, day);
    });
  };

  return (
    <div className="bg-white rounded-3xl shadow-lg border border-gray-100 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{format(currentDate, 'MMMM yyyy')}</h2>
          <p className="text-gray-600">Manage your schedule</p>
        </div>
        <div className="flex items-center space-x-3">
          <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors">
            Today
          </button>
          <button onClick={prevMonth} className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors">
            <ChevronLeft size={20} />
          </button>
          <button onClick={nextMonth} className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors">
            <ChevronRight size={20} />
          </button>
        </div>
      </div>
      
      {/* Calendar Grid */}
      <div className="grid grid-cols-7 gap-1 mb-4">
        {/* Day Headers */}
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
          <div key={day} className="p-3 text-center text-sm font-medium text-gray-500">
            {day}
          </div>
        ))}
        
        {/* Calendar Days */}
        {days.map((day) => (
          <div 
            key={day.toString()} 
            className={`p-3 text-center text-sm cursor-pointer rounded-xl transition-all duration-200 ${isSameMonth(day, currentDate) ? 'text-gray-700 hover:bg-gray-100' : 'text-gray-400'} ${isSameDay(day, new Date()) ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg' : ''}`}
          >
            {format(day, 'd')}
            {getEventsForDay(day).map((event) => (
              <div key={event.id} className="mt-1 text-xs text-gray-600">{event.summary}</div>
            ))}
          </div>
        ))}
      </div>
      
      {/* Upcoming Events */}
      <div className="border-t border-gray-100 pt-6">
        <h3 className="font-semibold text-gray-900 mb-4">Upcoming Events</h3>
        <div className="space-y-3">
          {events.map((event) => (
            <div key={event.id} className="flex items-center p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer">
              <div className={`w-3 h-3 rounded-full mr-3 bg-blue-500`}></div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">{event.summary}</p>
                <p className="text-sm text-gray-500">{format(new Date(event.start.dateTime), 'hh:mm a')} - {format(new Date(event.end.dateTime), 'hh:mm a')}</p>
              </div>
              <ChevronRight size={20} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CalendarView;