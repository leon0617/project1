import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import type { DebugEvent } from '@/types';

interface DebugEventDetailProps {
  event: DebugEvent;
  onClose: () => void;
}

export function DebugEventDetail({ event, onClose }: DebugEventDetailProps) {
  return (
    <Card>
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-semibold">Event Details</h3>
        <Button variant="secondary" size="sm" onClick={onClose}>
          ✕
        </Button>
      </div>

      <div className="space-y-4">
        <div>
          <h4 className="font-medium text-sm text-gray-700 mb-1">URL</h4>
          <p className="text-sm break-all">{event.url}</p>
        </div>

        <div>
          <h4 className="font-medium text-sm text-gray-700 mb-1">Timing</h4>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">DNS:</span>
              <span>{event.timing.dns.toFixed(0)}ms</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">TCP:</span>
              <span>{event.timing.tcp.toFixed(0)}ms</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">TLS:</span>
              <span>{event.timing.tls.toFixed(0)}ms</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">TTFB:</span>
              <span>{event.timing.ttfb.toFixed(0)}ms</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Download:</span>
              <span>{event.timing.download.toFixed(0)}ms</span>
            </div>
            <div className="flex justify-between font-semibold">
              <span className="text-gray-700">Total:</span>
              <span>{event.timing.total.toFixed(0)}ms</span>
            </div>
          </div>
        </div>

        <div>
          <h4 className="font-medium text-sm text-gray-700 mb-1">Request Headers</h4>
          <div className="bg-gray-50 p-2 rounded text-xs overflow-auto max-h-40">
            <pre>{JSON.stringify(event.requestHeaders, null, 2)}</pre>
          </div>
        </div>

        <div>
          <h4 className="font-medium text-sm text-gray-700 mb-1">Response Headers</h4>
          <div className="bg-gray-50 p-2 rounded text-xs overflow-auto max-h-40">
            <pre>{JSON.stringify(event.responseHeaders, null, 2)}</pre>
          </div>
        </div>

        {event.requestBody && (
          <div>
            <h4 className="font-medium text-sm text-gray-700 mb-1">Request Body</h4>
            <div className="bg-gray-50 p-2 rounded text-xs overflow-auto max-h-40">
              <pre>{event.requestBody}</pre>
            </div>
          </div>
        )}

        {event.responseBody && (
          <div>
            <h4 className="font-medium text-sm text-gray-700 mb-1">Response Body</h4>
            <div className="bg-gray-50 p-2 rounded text-xs overflow-auto max-h-40">
              <pre>{event.responseBody}</pre>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
