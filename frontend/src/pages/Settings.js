import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { PlayCircle, CheckCircle, XCircle, Clock } from 'lucide-react';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Settings = () => {
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${API}/scrapers/logs`);
      setLogs(response.data);
    } catch (error) {
      console.error('Error fetching logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const runScrapers = async () => {
    setRunning(true);
    toast.info('Starting scrapers...');

    try {
      const response = await axios.post(`${API}/scrapers/run`);
      toast.success(`Scrapers completed! Processed ${response.data.listings_processed} listings.`);
      await fetchLogs();
    } catch (error) {
      console.error('Error running scrapers:', error);
      toast.error('Failed to run scrapers');
    } finally {
      setRunning(false);
    }
  };

  const getStatusIcon = (status) => {
    if (status === 'success') return <CheckCircle className="h-5 w-5 text-green-600" />;
    if (status === 'error') return <XCircle className="h-5 w-5 text-red-600" />;
    return <Clock className="h-5 w-5 text-slate-400" />;
  };

  return (
    <div data-testid="settings-page">
      <div className="mb-8">
        <h1 className="font-heading text-4xl font-black tracking-tight text-slate-900 mb-2">
          Settings
        </h1>
        <p className="text-base text-slate-600">Manage scrapers and view logs</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <div className="bg-white border border-slate-200 rounded-md p-6 shadow-sm">
            <h2 className="font-heading text-xl font-semibold tracking-tight text-slate-900 mb-4">
              Scraper Control
            </h2>
            <p className="text-sm text-slate-600 mb-6">
              Manually trigger scrapers to fetch the latest machinery listings from all sources.
            </p>
            <Button
              onClick={runScrapers}
              disabled={running}
              data-testid="run-scraper-btn"
              className="w-full"
            >
              {running ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                  Running...
                </>
              ) : (
                <>
                  <PlayCircle className="mr-2 h-4 w-4" />
                  Run Scrapers Now
                </>
              )}
            </Button>
            <div className="mt-6 pt-6 border-t border-slate-200">
              <h3 className="text-sm font-semibold text-slate-900 mb-2">Automated Schedule</h3>
              <p className="text-sm text-slate-600">
                Scrapers run automatically every day at midnight.
              </p>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2">
          <div className="bg-white border border-slate-200 rounded-md shadow-sm">
            <div className="p-6 border-b border-slate-200">
              <h2 className="font-heading text-xl font-semibold tracking-tight text-slate-900">
                Scraper Logs
              </h2>
            </div>
            <div className="divide-y divide-slate-100" data-testid="scraper-logs">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-4 border-slate-900 border-t-transparent"></div>
                </div>
              ) : logs.length === 0 ? (
                <div className="p-12 text-center text-slate-500">
                  No logs available. Run the scraper to see results.
                </div>
              ) : (
                logs.map((log, index) => (
                  <div key={index} className="p-6 hover:bg-slate-50 transition-colors" data-testid="log-entry">
                    <div className="flex items-start gap-4">
                      <div className="mt-1">
                        {getStatusIcon(log.status)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="text-sm font-semibold text-slate-900">{log.source}</h3>
                          <span className="font-mono text-xs text-slate-500">
                            {new Date(log.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm text-slate-600 mb-2">{log.message}</p>
                        <div className="flex items-center gap-4 text-xs text-slate-500">
                          <span>Listings found: <span className="font-semibold text-slate-900">{log.listings_found}</span></span>
                          <span className={`inline-flex items-center px-2 py-0.5 rounded font-medium ${
                            log.status === 'success' 
                              ? 'bg-green-100 text-green-700' 
                              : 'bg-red-100 text-red-700'
                          }`}>
                            {log.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 bg-slate-100 border border-slate-200 rounded-md p-6">
        <h3 className="text-sm font-semibold text-slate-900 mb-2">About Scrapers</h3>
        <div className="text-sm text-slate-600 space-y-2">
          <p><strong>Current Sources:</strong> Machineseeker, Exapro</p>
          <p><strong>Status Detection:</strong> Listings not seen for 3 days are marked "Possibly Sold", after 7 days they're marked "Removed"</p>
          <p><strong>Price Tracking:</strong> All price changes are automatically logged for historical analysis</p>
        </div>
      </div>
    </div>
  );
};

export default Settings;
