import { useState } from 'react';
import { useSites, useDeleteSite } from '@/hooks/useApi';
import { Button } from '@/components/common/Button';
import { Card } from '@/components/common/Card';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { SiteForm } from './SiteForm';
import type { Site } from '@/types';

export function SiteList() {
  const { data: sites, isLoading } = useSites();
  const deleteSite = useDeleteSite();
  const [editingSite, setEditingSite] = useState<Site | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);

  if (isLoading) return <LoadingSpinner />;

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this site?')) {
      await deleteSite.mutateAsync(id);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Monitored Sites</h2>
        <Button onClick={() => setShowAddForm(true)}>Add Site</Button>
      </div>

      {showAddForm && (
        <Card className="mb-6">
          <SiteForm
            onClose={() => setShowAddForm(false)}
            onSuccess={() => setShowAddForm(false)}
          />
        </Card>
      )}

      {editingSite && (
        <Card className="mb-6">
          <SiteForm
            site={editingSite}
            onClose={() => setEditingSite(null)}
            onSuccess={() => setEditingSite(null)}
          />
        </Card>
      )}

      <div className="grid gap-4">
        {sites?.map((site) => (
          <Card key={site.id}>
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <h3 className="text-xl font-semibold">{site.name}</h3>
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      site.enabled
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {site.enabled ? 'Active' : 'Disabled'}
                  </span>
                </div>
                <p className="text-gray-600 mt-1">{site.url}</p>
                <p className="text-sm text-gray-500 mt-2">
                  Check interval: {site.checkInterval} seconds
                </p>
              </div>
              <div className="flex space-x-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setEditingSite(site)}
                >
                  Edit
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => handleDelete(site.id)}
                >
                  Delete
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
