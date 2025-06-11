"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

interface Event {
  id: string;
  summary: string;
  description?: string;
  start: string;
  end: string;
  location?: string;
  provider: string;
}

export default function CalendarView() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dateRange, setDateRange] = useState({
    from: new Date().toISOString().split("T")[0],
    to: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split("T")[0],
  });
  const router = useRouter();

  // Fetch events on component mount and when date range changes
  useEffect(() => {
    fetchEvents();
  }, [dateRange]);

  const fetchEvents = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/events?from=${dateRange.from}&to=${dateRange.to}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
        }
      );

      if (!response.ok) {
        if (response.status === 401) {
          // Handle unauthorized - redirect to login
          router.push("/login");
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setEvents(data.events || []);
    } catch (err) {
      console.error("Error fetching events:", err);
      setError("Failed to load events. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  const handleDateChange = (field: "from" | "to", value: string) => {
    setDateRange((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "numeric",
    }).format(date);
  };

  return (
    <div className="bg-white shadow rounded-lg p-4">
      <h2 className="text-xl font-semibold mb-4">Your Calendar</h2>

      {/* Date range selector */}
      <div className="flex flex-wrap mb-4 gap-4">
        <div>
          <label htmlFor="from" className="block text-sm font-medium text-gray-700 mb-1">
            From
          </label>
          <input
            type="date"
            id="from"
            value={dateRange.from}
            onChange={(e) => handleDateChange("from", e.target.value)}
            className="p-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label htmlFor="to" className="block text-sm font-medium text-gray-700 mb-1">
            To
          </label>
          <input
            type="date"
            id="to"
            value={dateRange.to}
            onChange={(e) => handleDateChange("to", e.target.value)}
            className="p-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div className="flex items-end">
          <button
            onClick={fetchEvents}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-2 text-gray-500">Loading events...</p>
        </div>
      ) : events.length === 0 ? (
        <div className="text-center py-8 bg-gray-50 rounded">
          <p className="text-gray-500">No events found for the selected date range.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white">
            <thead className="bg-gray-100">
              <tr>
                <th className="py-2 px-4 text-left text-gray-700 font-medium">Event</th>
                <th className="py-2 px-4 text-left text-gray-700 font-medium">Start</th>
                <th className="py-2 px-4 text-left text-gray-700 font-medium">End</th>
                <th className="py-2 px-4 text-left text-gray-700 font-medium">Location</th>
                <th className="py-2 px-4 text-left text-gray-700 font-medium">Provider</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {events.map((event) => (
                <tr key={event.id} className="hover:bg-gray-50">
                  <td className="py-3 px-4">{event.summary}</td>
                  <td className="py-3 px-4">{formatDate(event.start)}</td>
                  <td className="py-3 px-4">{formatDate(event.end)}</td>
                  <td className="py-3 px-4">{event.location || "—"}</td>
                  <td className="py-3 px-4 capitalize">
                    <span
                      className={`inline-block px-2 py-1 text-xs rounded-full ${
                        event.provider === "google"
                          ? "bg-blue-100 text-blue-800"
                          : "bg-green-100 text-green-800"
                      }`}
                    >
                      {event.provider}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
} 