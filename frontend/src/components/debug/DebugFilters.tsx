import { useSites } from '@/hooks/useApi';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import type { FilterOptions } from '@/types';

interface DebugFiltersProps {
  filters: FilterOptions;
  onFiltersChange: (filters: FilterOptions) => void;
}

export function DebugFilters({ filters, onFiltersChange }: DebugFiltersProps) {
  const { data: sites } = useSites();

  const handleChange = (key: keyof FilterOptions, value: string | number | undefined) => {
    onFiltersChange({
      ...filters,
      [key]: value || undefined,
    });
  };

  const handleReset = () => {
    onFiltersChange({});
  };

  return (
    <Card>
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Site
          </label>
          <select
            value={filters.siteId || ''}
            onChange={(e) => handleChange('siteId', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Sites</option>
            {sites?.map((site) => (
              <option key={site.id} value={site.id}>
                {site.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Start Date
          </label>
          <input
            type="datetime-local"
            value={filters.startDate || ''}
            onChange={(e) => handleChange('startDate', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            End Date
          </label>
          <input
            type="datetime-local"
            value={filters.endDate || ''}
            onChange={(e) => handleChange('endDate', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Status Code
          </label>
          <input
            type="number"
            value={filters.statusCode || ''}
            onChange={(e) => handleChange('statusCode', e.target.value ? parseInt(e.target.value) : undefined)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g. 200"
          />
        </div>

        <div className="flex items-end">
          <Button variant="secondary" onClick={handleReset} className="w-full">
            Reset Filters
          </Button>
        </div>
      </div>
    </Card>
  );
}
