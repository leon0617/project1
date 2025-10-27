import { format } from 'date-fns';
import type { DebugEvent } from '@/types';

interface DebugEventTableProps {
  events: DebugEvent[];
  onSelectEvent: (event: DebugEvent) => void;
  selectedEventId?: string;
}

export function DebugEventTable({ events, onSelectEvent, selectedEventId }: DebugEventTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Time
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Site
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Method
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Response Time
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {events.map((event) => (
            <tr
              key={event.id}
              onClick={() => onSelectEvent(event)}
              className={`cursor-pointer hover:bg-gray-50 ${
                selectedEventId === event.id ? 'bg-blue-50' : ''
              }`}
            >
              <td className="px-4 py-3 whitespace-nowrap text-sm">
                {format(new Date(event.timestamp), 'HH:mm:ss')}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm">
                {event.siteName}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm font-medium">
                {event.method}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm">
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    event.statusCode >= 200 && event.statusCode < 300
                      ? 'bg-green-100 text-green-800'
                      : event.statusCode >= 400
                      ? 'bg-red-100 text-red-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}
                >
                  {event.statusCode}
                </span>
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm">
                {event.responseTime.toFixed(0)}ms
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
