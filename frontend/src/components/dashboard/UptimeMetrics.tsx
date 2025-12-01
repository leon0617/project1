import { useUptimeMetrics } from '@/hooks/useApi';
import { Card } from '@/components/common/Card';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';

export function UptimeMetrics() {
  const { data: metrics, isLoading } = useUptimeMetrics();

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {metrics?.map((metric) => (
        <Card key={metric.siteId}>
          <div className="flex justify-between items-start mb-4">
            <h3 className="font-semibold text-lg">{metric.siteName}</h3>
            <span
              className={`px-2 py-1 text-xs rounded-full ${
                metric.uptime >= 99
                  ? 'bg-green-100 text-green-800'
                  : metric.uptime >= 95
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {metric.uptime.toFixed(2)}% uptime
            </span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Total Checks:</span>
              <span className="font-medium">{metric.totalChecks}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Successful:</span>
              <span className="font-medium text-green-600">
                {metric.successfulChecks}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Failed:</span>
              <span className="font-medium text-red-600">
                {metric.failedChecks}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Avg Response:</span>
              <span className="font-medium">
                {metric.avgResponseTime.toFixed(0)}ms
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-2">
              Last check: {new Date(metric.lastCheckAt).toLocaleString()}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
