import { useResponseTimes } from '@/hooks/useApi';
import { Card } from '@/components/common/Card';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';

interface ResponseTimeChartProps {
  siteId: string;
  hours?: number;
}

export function ResponseTimeChart({ siteId, hours = 24 }: ResponseTimeChartProps) {
  const { data, isLoading } = useResponseTimes(siteId, hours);

  if (isLoading) return <LoadingSpinner />;
  if (!data || data.length === 0) {
    return <Card><p className="text-gray-500">No data available</p></Card>;
  }

  const chartData = data.map((point) => ({
    time: format(new Date(point.timestamp), 'HH:mm'),
    responseTime: point.responseTime,
    statusCode: point.statusCode,
  }));

  return (
    <Card title="Response Time (Last 24 Hours)">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis label={{ value: 'Response Time (ms)', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="responseTime"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            name="Response Time (ms)"
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}
