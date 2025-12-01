import { useState } from 'react';
import { useSLAReports } from '@/hooks/useApi';
import { Card } from '@/components/common/Card';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';

export function SLAReports() {
  const [period, setPeriod] = useState('month');
  const { data: reports, isLoading } = useSLAReports(period);

  if (isLoading) return <LoadingSpinner />;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">SLA Reports</h2>
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="day">Last Day</option>
          <option value="week">Last Week</option>
          <option value="month">Last Month</option>
          <option value="year">Last Year</option>
        </select>
      </div>

      <div className="grid gap-4">
        {reports?.map((report) => (
          <Card key={report.siteId}>
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-semibold">{report.siteName}</h3>
              <span className="text-sm text-gray-500">Period: {report.period}</span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div>
                <div className="text-sm text-gray-600 mb-1">Uptime</div>
                <div className="text-2xl font-bold text-blue-600">
                  {report.uptime.toFixed(2)}%
                </div>
              </div>

              <div>
                <div className="text-sm text-gray-600 mb-1">Availability</div>
                <div className="text-2xl font-bold text-green-600">
                  {report.availability.toFixed(2)}%
                </div>
              </div>

              <div>
                <div className="text-sm text-gray-600 mb-1">MTTR</div>
                <div className="text-2xl font-bold text-yellow-600">
                  {report.mttr.toFixed(0)}m
                </div>
                <div className="text-xs text-gray-500">Mean Time to Repair</div>
              </div>

              <div>
                <div className="text-sm text-gray-600 mb-1">MTBF</div>
                <div className="text-2xl font-bold text-purple-600">
                  {report.mtbf.toFixed(0)}m
                </div>
                <div className="text-xs text-gray-500">Mean Time Between Failures</div>
              </div>

              <div>
                <div className="text-sm text-gray-600 mb-1">Incidents</div>
                <div className="text-2xl font-bold text-red-600">
                  {report.incidents}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
