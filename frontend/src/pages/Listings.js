import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link, useSearchParams } from 'react-router-dom';
import { Search, Filter, ExternalLink, ChevronDown } from 'lucide-react';
import { Button } from '../components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Input } from '../components/ui/input';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const statusColors = {
  'Active': 'bg-emerald-100 text-emerald-700 border-emerald-200',
  'Possibly Sold': 'bg-slate-100 text-slate-600 border-slate-200',
  'Removed': 'bg-red-100 text-red-700 border-red-200'
};

export const Listings = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [machines, setMachines] = useState([]);
  const [filters, setFilters] = useState({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get('category') || '');
  const [selectedManufacturer, setSelectedManufacturer] = useState('');
  const [selectedStatus, setSelectedStatus] = useState(searchParams.get('status') || '');
  const [sortBy, setSortBy] = useState('last_seen');

  useEffect(() => {
    fetchFilters();
  }, []);

  useEffect(() => {
    fetchMachines();
  }, [selectedCategory, selectedManufacturer, selectedStatus, sortBy, search]);

  const fetchFilters = async () => {
    try {
      const response = await axios.get(`${API}/filters/options`);
      setFilters(response.data);
    } catch (error) {
      console.error('Error fetching filters:', error);
    }
  };

  const fetchMachines = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedCategory) params.append('category', selectedCategory);
      if (selectedManufacturer) params.append('manufacturer', selectedManufacturer);
      if (selectedStatus) params.append('status', selectedStatus);
      if (search) params.append('search', search);
      params.append('sort_by', sortBy);
      params.append('sort_order', 'desc');

      const response = await axios.get(`${API}/machines?${params.toString()}`);
      setMachines(response.data);
    } catch (error) {
      console.error('Error fetching machines:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchMachines();
  };

  const clearFilters = () => {
    setSelectedCategory('');
    setSelectedManufacturer('');
    setSelectedStatus('');
    setSearch('');
    setSortBy('last_seen');
  };

  return (
    <div data-testid="listings-page">
      <div className="mb-8">
        <h1 className="font-heading text-4xl font-black tracking-tight text-slate-900 mb-2">
          All Listings
        </h1>
        <p className="text-base text-slate-600">Browse and filter machinery listings</p>
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-4 mb-6 shadow-sm" data-testid="filters-panel">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <form onSubmit={handleSearchSubmit} className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                data-testid="search-input"
                type="text"
                placeholder="Search by title or model..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
          </form>

          <Select value={selectedCategory} onValueChange={setSelectedCategory}>
            <SelectTrigger data-testid="category-filter">
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              {filters.categories?.map((cat) => (
                <SelectItem key={cat} value={cat}>{cat}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={selectedStatus} onValueChange={setSelectedStatus}>
            <SelectTrigger data-testid="status-filter">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              {filters.statuses?.map((status) => (
                <SelectItem key={status} value={status}>{status}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Select value={selectedManufacturer} onValueChange={setSelectedManufacturer}>
              <SelectTrigger data-testid="manufacturer-filter" className="w-48">
                <SelectValue placeholder="Manufacturer" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Manufacturers</SelectItem>
                {filters.manufacturers?.map((mfr) => (
                  <SelectItem key={mfr} value={mfr}>{mfr}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger data-testid="sort-by-select" className="w-48">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="last_seen">Last Seen</SelectItem>
                <SelectItem value="first_seen">First Seen</SelectItem>
                <SelectItem value="current_price">Price</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button
            variant="ghost"
            onClick={clearFilters}
            data-testid="clear-filters-btn"
            className="text-slate-600"
          >
            Clear Filters
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64" data-testid="listings-loading">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-slate-900 border-t-transparent"></div>
        </div>
      ) : machines.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-md p-12 text-center" data-testid="no-listings">
          <p className="text-slate-600 mb-4">No listings found</p>
          <Link to="/settings">
            <Button data-testid="trigger-scraper-btn">Run Scraper</Button>
          </Link>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-md shadow-sm overflow-hidden" data-testid="listings-table">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200 sticky top-0">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Machine</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Category</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Price</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Seller</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Last Seen</th>
                <th className="px-6 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {machines.map((machine) => (
                <tr key={machine.machine_id} className="hover:bg-slate-50 transition-colors" data-testid="machine-row">
                  <td className="px-6 py-4">
                    <Link to={`/machine/${machine.machine_id}`} className="font-medium text-slate-900 hover:text-slate-600">
                      {machine.title}
                    </Link>
                    {machine.manufacturer && (
                      <p className="text-xs text-slate-500 mt-1">{machine.manufacturer}</p>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600">{machine.category}</td>
                  <td className="px-6 py-4">
                    {machine.current_price ? (
                      <span className="font-mono text-sm font-semibold text-slate-900">
                        {machine.currency} {machine.current_price.toLocaleString()}
                      </span>
                    ) : (
                      <span className="text-sm text-slate-400">N/A</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600">{machine.seller}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium border ${statusColors[machine.status]}`}>
                      {machine.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono text-xs text-slate-500">
                    {new Date(machine.last_seen).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <a
                      href={machine.listing_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      data-testid="external-link"
                      className="text-slate-400 hover:text-slate-900 transition-colors"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {machines.length > 0 && (
        <div className="mt-4 text-sm text-slate-600" data-testid="results-count">
          Showing {machines.length} listings
        </div>
      )}
    </div>
  );
};

export default Listings;
