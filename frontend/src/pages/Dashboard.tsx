import { useSites } from '@/hooks/useApi';
import { UptimeMetrics } from '@/components/dashboard/UptimeMetrics';
import { ResponseTimeChart } from '@/components/dashboard/ResponseTimeChart';
import { DowntimeTimeline } from '@/components/dashboard/DowntimeTimeline';

export function Dashboard() {
  const { data: sites } = useSites();
  const firstSite = sites?.[0];

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
      
      <div className="space-y-6">
        <UptimeMetrics />
        
        {firstSite && (
          <ResponseTimeChart siteId={firstSite.id} />
        )}
        
        <DowntimeTimeline />
      </div>
    </div>
  );
}
