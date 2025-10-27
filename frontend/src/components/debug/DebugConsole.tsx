import { useState, useEffect } from 'react';
import { useDebugEvents } from '@/hooks/useApi';
import { Card } from '@/components/common/Card';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { DebugEventTable } from './DebugEventTable';
import { DebugEventDetail } from './DebugEventDetail';
import { DebugFilters } from './DebugFilters';
import { createEventSource } from '@/lib/api';
import type { DebugEvent, FilterOptions } from '@/types';

export function DebugConsole() {
  const [filters, setFilters] = useState<FilterOptions>({});
  const [selectedEvent, setSelectedEvent] = useState<DebugEvent | null>(null);
  const [liveEvents, setLiveEvents] = useState<DebugEvent[]>([]);
  const { data: historicalEvents, isLoading } = useDebugEvents(filters);

  useEffect(() => {
    const eventSource = createEventSource('/api/debug/stream');
    
    eventSource.onmessage = (event) => {
      const newEvent = JSON.parse(event.data) as DebugEvent;
      setLiveEvents((prev) => [newEvent, ...prev].slice(0, 100));
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  const allEvents = [...liveEvents, ...(historicalEvents || [])];

  if (isLoading && !liveEvents.length) return <LoadingSpinner />;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Debug Console</h2>
      
      <DebugFilters filters={filters} onFiltersChange={setFilters} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        <div className="lg:col-span-2">
          <Card>
            <DebugEventTable
              events={allEvents}
              onSelectEvent={setSelectedEvent}
              selectedEventId={selectedEvent?.id}
            />
          </Card>
        </div>

        {selectedEvent && (
          <div className="lg:col-span-1">
            <DebugEventDetail
              event={selectedEvent}
              onClose={() => setSelectedEvent(null)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
