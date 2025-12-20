import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, Link } from 'react-router-dom';
import { ExternalLink, ArrowLeft, Calendar, MapPin, DollarSign } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Button } from '../components/ui/button';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const statusColors = {
  'Active': 'bg-emerald-100 text-emerald-700 border-emerald-200',
  'Possibly Sold': 'bg-slate-100 text-slate-600 border-slate-200',
  'Removed': 'bg-red-100 text-red-700 border-red-200'
};

export const MachineDetail = () => {
  const { id } = useParams();
  const [machine, setMachine] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMachineDetails();
    fetchPriceHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const fetchMachineDetails = async () => {
    try {
      const response = await axios.get(`${API}/machines/${id}`);
      setMachine(response.data);
    } catch (error) {
      console.error('Error fetching machine details:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPriceHistory = async () => {
    try {
      const response = await axios.get(`${API}/machines/${id}/price-history`);
      setPriceHistory(response.data);
    } catch (error) {
      console.error('Error fetching price history:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="machine-detail-loading">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-slate-900 border-t-transparent"></div>
      </div>
    );
  }

  if (!machine) {
    return (
      <div className="text-center py-12" data-testid="machine-not-found">
        <p className="text-slate-600 mb-4">Machine not found</p>
        <Link to="/listings">
          <Button>Back to Listings</Button>
        </Link>
      </div>
    );
  }

  const chartData = priceHistory.map(record => ({
    date: new Date(record.timestamp).toLocaleDateString(),
    price: record.price
  }));

  return (
    <div data-testid="machine-detail-page">
      <Link to="/listings" className="inline-flex items-center gap-2 text-slate-600 hover:text-slate-900 mb-6" data-testid="back-to-listings">
        <ArrowLeft className="h-4 w-4" />
        Back to Listings
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-8">
          <div className="bg-white border border-slate-200 rounded-md p-8 shadow-sm mb-6">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h1 className="font-heading text-3xl font-bold tracking-tight text-slate-900 mb-2" data-testid="machine-title">
                  {machine.title}
                </h1>
                <div className="flex items-center gap-4 text-sm text-slate-600">
                  {machine.manufacturer && (
                    <span className="font-medium">{machine.manufacturer}</span>
                  )}
                  {machine.year && (
                    <span className="flex items-center gap-1">
                      <Calendar className="h-4 w-4" />
                      {machine.year}
                    </span>
                  )}
                  {machine.location && (
                    <span className="flex items-center gap-1">
                      <MapPin className="h-4 w-4" />
                      {machine.location}
                    </span>
                  )}
                </div>
              </div>
              <span className={`inline-flex items-center px-3 py-1.5 rounded text-sm font-medium border ${statusColors[machine.status]}`} data-testid="machine-status">
                {machine.status}
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 py-6 border-t border-b border-slate-200">
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">Category</p>
                <p className="text-sm font-semibold text-slate-900">{machine.category}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">Seller</p>
                <p className="text-sm font-semibold text-slate-900">{machine.seller}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">Source</p>
                <p className="text-sm font-semibold text-slate-900">{machine.source}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">Current Price</p>
                {machine.current_price ? (
                  <p className="font-mono text-sm font-bold text-slate-900" data-testid="machine-price">
                    {machine.currency} {machine.current_price.toLocaleString()}
                  </p>
                ) : (
                  <p className="text-sm text-slate-400">N/A</p>
                )}
              </div>
            </div>

            <div className="mt-6">
              <a
                href={machine.listing_url}
                target="_blank"
                rel="noopener noreferrer"
                data-testid="view-listing-btn"
              >
                <Button className="w-full sm:w-auto">
                  View on {machine.source}
                  <ExternalLink className="ml-2 h-4 w-4" />
                </Button>
              </a>
            </div>
          </div>

          {chartData.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-md p-8 shadow-sm" data-testid="price-history-chart">
              <h2 className="font-heading text-xl font-semibold tracking-tight text-slate-900 mb-6">
                Price History
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12, fill: '#64748b' }}
                    stroke="#cbd5e1"
                  />
                  <YAxis
                    tick={{ fontSize: 12, fill: '#64748b' }}
                    stroke="#cbd5e1"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      border: '1px solid #e2e8f0',
                      borderRadius: '6px',
                      fontSize: '12px'
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="price"
                    stroke="#0f172a"
                    strokeWidth={2}
                    dot={{ fill: '#0f172a', r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <div className="lg:col-span-4">
          <div className="bg-white border border-slate-200 rounded-md p-6 shadow-sm">
            <h2 className="font-heading text-xl font-semibold tracking-tight text-slate-900 mb-4">
              Timeline
            </h2>
            <div className="space-y-4">
              <div className="flex items-start gap-3 pb-4 border-b border-slate-100">
                <div className="mt-1 p-2 bg-blue-50 rounded">
                  <Calendar className="h-4 w-4 text-blue-600" />
                </div>
                <div>
                  <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">First Seen</p>
                  <p className="font-mono text-sm font-semibold text-slate-900">
                    {new Date(machine.first_seen).toLocaleString()}
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="mt-1 p-2 bg-green-50 rounded">
                  <Calendar className="h-4 w-4 text-green-600" />
                </div>
                <div>
                  <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">Last Seen</p>
                  <p className="font-mono text-sm font-semibold text-slate-900">
                    {new Date(machine.last_seen).toLocaleString()}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {priceHistory.length > 1 && (
            <div className="bg-white border border-slate-200 rounded-md p-6 shadow-sm mt-6" data-testid="price-stats">
              <h2 className="font-heading text-xl font-semibold tracking-tight text-slate-900 mb-4">
                Price Stats
              </h2>
              <div className="space-y-3">
                <div className="flex items-center justify-between py-2 border-b border-slate-100">
                  <span className="text-sm font-medium text-slate-600">Price Changes</span>
                  <span className="font-mono text-sm font-semibold text-slate-900">
                    {priceHistory.length}
                  </span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm font-medium text-slate-600">Time on Market</span>
                  <span className="font-mono text-sm font-semibold text-slate-900">
                    {Math.ceil((new Date(machine.last_seen) - new Date(machine.first_seen)) / (1000 * 60 * 60 * 24))} days
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MachineDetail;
