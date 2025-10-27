import { useDowntimeEvents } from '@/hooks/useApi';
import { Card } from '@/components/common/Card';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { format } from 'date-fns';

interface DowntimeTimelineProps {
  siteId?: string;
}

export function DowntimeTimeline({ siteId }: DowntimeTimelineProps) {
  const { data: events, isLoading } = useDowntimeEvents(siteId);

  if (isLoading) return <LoadingSpinner />;

  return (
    <Card title="Downtime Events">
      {events && events.length > 0 ? (
        <div className="space-y-4">
          {events.map((event) => (
            <div key={event.id} className="border-l-4 border-red-500 pl-4 py-2">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-semibold">{event.siteName}</h4>
                  <p className="text-sm text-gray-600">
                    Started: {format(new Date(event.startTime), 'PPp')}
                  </p>
                  {event.endTime && (
                    <p className="text-sm text-gray-600">
                      Ended: {format(new Date(event.endTime), 'PPp')}
                    </p>
                  )}
                  {event.duration && (
                    <p className="text-sm text-gray-600">
                      Duration: {Math.round(event.duration / 60)} minutes
                    </p>
                  )}
                </div>
                <div className="text-right">
                  {event.statusCode && (
                    <span className="text-sm font-medium text-red-600">
                      Status: {event.statusCode}
                    </span>
                  )}
                  {event.errorMessage && (
                    <p className="text-xs text-gray-500 mt-1">
                      {event.errorMessage}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-gray-500">No downtime events recorded</p>
      )}
    </Card>
  );
}
