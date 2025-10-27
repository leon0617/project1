import { useState } from 'react';
import { useCreateSite, useUpdateSite } from '@/hooks/useApi';
import { Button } from '@/components/common/Button';
import type { Site } from '@/types';

interface SiteFormProps {
  site?: Site;
  onClose: () => void;
  onSuccess: () => void;
}

export function SiteForm({ site, onClose, onSuccess }: SiteFormProps) {
  const [formData, setFormData] = useState({
    name: site?.name || '',
    url: site?.url || '',
    checkInterval: site?.checkInterval || 300,
    enabled: site?.enabled ?? true,
  });

  const createSite = useCreateSite();
  const updateSite = useUpdateSite();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (site) {
        await updateSite.mutateAsync({ id: site.id, data: formData });
      } else {
        await createSite.mutateAsync(formData);
      }
      onSuccess();
    } catch (error) {
      console.error('Failed to save site:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h3 className="text-lg font-semibold mb-4">
        {site ? 'Edit Site' : 'Add New Site'}
      </h3>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Name
        </label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          URL
        </label>
        <input
          type="url"
          value={formData.url}
          onChange={(e) => setFormData({ ...formData, url: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Check Interval (seconds)
        </label>
        <input
          type="number"
          value={formData.checkInterval}
          onChange={(e) =>
            setFormData({ ...formData, checkInterval: parseInt(e.target.value) })
          }
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
          min="60"
        />
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          id="enabled"
          checked={formData.enabled}
          onChange={(e) =>
            setFormData({ ...formData, enabled: e.target.checked })
          }
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor="enabled" className="ml-2 block text-sm text-gray-700">
          Enabled
        </label>
      </div>

      <div className="flex justify-end space-x-2 pt-4">
        <Button type="button" variant="secondary" onClick={onClose}>
          Cancel
        </Button>
        <Button type="submit">
          {site ? 'Update' : 'Create'}
        </Button>
      </div>
    </form>
  );
}
