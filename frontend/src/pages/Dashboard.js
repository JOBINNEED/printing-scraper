import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { TrendingDown, Package, AlertCircle, Activity, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Dashboard = () => {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOverview();
  }, []);

  const fetchOverview = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/overview`);
      setOverview(response.data);
    } catch (error) {
      console.error('Error fetching overview:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="dashboard-loading">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-slate-900 border-t-transparent"></div>
      </div>
    );
  }

  const stats = [
    {
      name: 'New Listings',
      value: overview?.new_listings || 0,
      icon: Package,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
      testId: 'stat-new-listings'
    },
    {
      name: 'Price Drops',
      value: overview?.price_drops || 0,
      icon: TrendingDown,
      color: 'text-green-600',
      bg: 'bg-green-50',
      testId: 'stat-price-drops'
    },
    {
      name: 'Likely Sold',
      value: overview?.likely_sold || 0,
      icon: AlertCircle,
      color: 'text-orange-600',
      bg: 'bg-orange-50',
      testId: 'stat-likely-sold'
    },
    {
      name: 'Active Listings',
      value: overview?.total_active || 0,
      icon: Activity,
      color: 'text-slate-600',
      bg: 'bg-slate-50',
      testId: 'stat-active-listings'
    },
  ];

  return (
    <div data-testid="dashboard-page">
      <div className="mb-8">
        <h1 className="font-heading text-4xl font-black tracking-tight text-slate-900 mb-2">
          Market Overview
        </h1>
        <p className="text-base text-slate-600">Industrial printing & packaging machinery intelligence</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.name}
              data-testid={stat.testId}
              className="bg-white border border-slate-200 rounded-md p-6 shadow-sm hover:shadow-md transition-shadow duration-200"
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-md ${stat.bg}`}>
                  <Icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-600 mb-1">{stat.name}</p>
                <p className="font-mono text-3xl font-bold text-slate-900">{stat.value}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 rounded-md p-6 shadow-sm" data-testid="category-breakdown">
          <h2 className="font-heading text-xl font-semibold tracking-tight text-slate-900 mb-4">
            Category Breakdown
          </h2>
          {overview?.category_counts && Object.keys(overview.category_counts).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(overview.category_counts).map(([category, count]) => (
                <div key={category} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
                  <span className="text-sm font-medium text-slate-700">{category}</span>
                  <span className="font-mono text-sm font-semibold text-slate-900 bg-slate-100 px-3 py-1 rounded">
                    {count}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">No categories available</p>
          )}
        </div>

        <div className="bg-white border border-slate-200 rounded-md p-6 shadow-sm">
          <h2 className="font-heading text-xl font-semibold tracking-tight text-slate-900 mb-4">
            Quick Actions
          </h2>
          <div className="space-y-3">
            <Link
              to="/listings?status=Active"
              data-testid="quick-action-view-active"
              className="flex items-center justify-between p-4 border border-slate-200 rounded-md hover:bg-slate-50 transition-colors group"
            >
              <span className="text-sm font-medium text-slate-700">View Active Listings</span>
              <ArrowUpRight className="h-4 w-4 text-slate-400 group-hover:text-slate-900" />
            </Link>
            <Link
              to="/listings?status=Possibly Sold"
              data-testid="quick-action-view-sold"
              className="flex items-center justify-between p-4 border border-slate-200 rounded-md hover:bg-slate-50 transition-colors group"
            >
              <span className="text-sm font-medium text-slate-700">View Likely Sold</span>
              <ArrowUpRight className="h-4 w-4 text-slate-400 group-hover:text-slate-900" />
            </Link>
            <Link
              to="/settings"
              data-testid="quick-action-run-scraper"
              className="flex items-center justify-between p-4 border border-slate-200 rounded-md hover:bg-slate-50 transition-colors group"
            >
              <span className="text-sm font-medium text-slate-700">Run Scraper</span>
              <ArrowUpRight className="h-4 w-4 text-slate-400 group-hover:text-slate-900" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
