import React, { useEffect, useState } from 'react';
import Button from '../components/ui/Button';

interface OutboxJob {
  job_id: string;
  service: string;
  payload: any;
  last_error: string;
  attempts: number;
  contact?: {
    id: string;
    name: string;
    email: string;
    notes: string;
  };
}

const OutboxReview: React.FC = () => {
  const [jobs, setJobs] = useState<OutboxJob[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await fetch('/outbox/failed');
      if (!res.ok) throw new Error(`Error fetching jobs: ${res.status}`);
      const data = await res.json();
      setJobs(data);
    } catch (err) {
      console.error(err);
      alert('Failed to load failed jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleAction = async (jobId: string, action: 'requeue' | 'mark-sent') => {
    try {
      const res = await fetch(`/outbox/${jobId}/${action}`, { method: 'POST' });
      if (!res.ok) throw new Error(`${action} failed: ${res.status}`);
      alert(`${action} succeeded for ${jobId}`);
      fetchJobs();
    } catch (err) {
      console.error(err);
      alert(`${action} failed for ${jobId}`);
    }
  };

  if (loading) return <div className="p-6">Loading...</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Failed Outbox Jobs</h1>
      <table className="min-w-full bg-white">
        <thead>
          <tr>
            <th className="px-4 py-2">Job ID</th>
            <th className="px-4 py-2">Service</th>
            <th className="px-4 py-2">Attempts</th>
            <th className="px-4 py-2">Last Error</th>
            <th className="px-4 py-2">Contact</th>
            <th className="px-4 py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.job_id} className="border-t">
              <td className="px-4 py-2">{job.job_id}</td>
              <td className="px-4 py-2">{job.service}</td>
              <td className="px-4 py-2">{job.attempts}</td>
              <td className="px-4 py-2">{job.last_error}</td>
              <td className="px-4 py-2">
                {job.contact ? (
                  <div>
                    {job.contact.name} (<a className="text-blue-500" href={`mailto:${job.contact.email}`}>{job.contact.email}</a>)
                  </div>
                ) : (
                  <span className="text-gray-500">Unknown</span>
                )}
              </td>
              <td className="px-4 py-2 space-x-2">
                <Button onClick={() => handleAction(job.job_id, 'requeue')} className="bg-yellow-500 hover:bg-yellow-600">
                  Requeue
                </Button>
                <Button onClick={() => handleAction(job.job_id, 'mark-sent')} className="bg-green-500 hover:bg-green-600">
                  Mark Sent
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default OutboxReview;
