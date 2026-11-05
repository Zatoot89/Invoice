import { useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Card, CardBody, CardHeader } from '@nextui-org/react';
import { 
  BanknotesIcon, 
  DocumentTextIcon, 
  UserGroupIcon,
  ClockIcon,
  ChartBarIcon,
  ArrowUpIcon,
  ArrowDownIcon
} from '@heroicons/react/24/outline';

import DashboardLayout from '@/components/layout/DashboardLayout';
import StatsCard from '@/components/dashboard/StatsCard';
import RevenueChart from '@/components/dashboard/RevenueChart';
import RecentInvoices from '@/components/dashboard/RecentInvoices';
import { DashboardSummary } from '@/types';

// Mock data - replace with actual API calls
const mockStats: DashboardSummary = {
  total_revenue: 125000,
  total_invoices: 45,
  paid_invoices: 32,
  pending_invoices: 8,
  overdue_invoices: 5,
  total_customers: 15,
  average_invoice_value: 2777.78,
  collection_rate: 0.85,
  revenue_growth: 0.15,
  invoice_growth: 0.12,
};

const mockRevenueData = [
  { month: 'Jan', revenue: 30000, invoices: 12 },
  { month: 'Feb', revenue: 45000, invoices: 18 },
  { month: 'Mar', revenue: 50000, invoices: 15 },
  { month: 'Apr', revenue: 38000, invoices: 14 },
  { month: 'May', revenue: 52000, invoices: 20 },
  { month: 'Jun', revenue: 48000, invoices: 16 },
];

export default function Dashboard() {
  const [timeRange, setTimeRange] = useState('6m');
  
  return (
    <>
      <Helmet>
        <title>Dashboard - InvoiceFlow Pro</title>
        <meta name="description" content="InvoiceFlow Pro dashboard with analytics and insights" />
      </Helmet>
      
      <DashboardLayout>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Dashboard
              </h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Welcome back! Here's an overview of your business.
              </p>
            </div>
            
            <div className="flex items-center space-x-3">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="input-primary text-sm"
              >
                <option value="1m">Last month</option>
                <option value="3m">Last 3 months</option>
                <option value="6m">Last 6 months</option>
                <option value="1y">Last year</option>
              </select>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <StatsCard
              title="Total Revenue"
              value={`$${mockStats.total_revenue.toLocaleString()}`}
              change={mockStats.revenue_growth}
              changeLabel={`${(mockStats.revenue_growth * 100).toFixed(1)}% from last month`}
              icon={BanknotesIcon}
              color="primary"
            />
            
            <StatsCard
              title="Total Invoices"
              value={mockStats.total_invoices.toString()}
              change={mockStats.invoice_growth}
              changeLabel={`${(mockStats.invoice_growth * 100).toFixed(1)}% from last month`}
              icon={DocumentTextIcon}
              color="secondary"
            />
            
            <StatsCard
              title="Paid Invoices"
              value={mockStats.paid_invoices.toString()}
              change={0.08}
              changeLabel="8% from last month"
              icon={ChartBarIcon}
              color="success"
            />
            
            <StatsCard
              title="Customers"
              value={mockStats.total_customers.toString()}
              change={0.05}
              changeLabel="5% from last month"
              icon={UserGroupIcon}
              color="warning"
            />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* Revenue Chart */}
            <div className="lg:col-span-2">
              <Card>
                <CardHeader className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      Revenue Overview
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Monthly revenue and invoice trends
                    </p>
                  </div>
                </CardHeader>
                <CardBody>
                  <RevenueChart data={mockRevenueData} />
                </CardBody>
              </Card>
            </div>

            {/* Key Metrics */}
            <div className="space-y-6">
              {/* Collection Rate */}
              <Card>
                <CardBody className="text-center">
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {(mockStats.collection_rate * 100).toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Collection Rate
                  </div>
                  <div className="mt-2 flex items-center justify-center text-sm text-green-600">
                    <ArrowUpIcon className="mr-1 h-4 w-4" />
                    +3.2% from last month
                  </div>
                </CardBody>
              </Card>

              {/* Average Invoice Value */}
              <Card>
                <CardBody className="text-center">
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    ${mockStats.average_invoice_value.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Average Invoice
                  </div>
                  <div className="mt-2 flex items-center justify-center text-sm text-green-600">
                    <ArrowUpIcon className="mr-1 h-4 w-4" />
                    +12.5% from last month
                  </div>
                </CardBody>
              </Card>

              {/* Overdue Invoices */}
              <Card>
                <CardBody className="text-center">
                  <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                    {mockStats.overdue_invoices}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Overdue Invoices
                  </div>
                  <div className="mt-2 flex items-center justify-center text-sm text-red-600">
                    <ClockIcon className="mr-1 h-4 w-4" />
                    Requires attention
                  </div>
                </CardBody>
              </Card>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Recent Invoices */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Recent Invoices
                </h3>
              </CardHeader>
              <CardBody>
                <RecentInvoices />
              </CardBody>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Quick Actions
                </h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-3">
                  <button className="btn-primary w-full">
                    Create New Invoice
                  </button>
                  <button className="btn-secondary w-full">
                    Add Customer
                  </button>
                  <button className="btn-secondary w-full">
                    Record Payment
                  </button>
                  <button className="btn-secondary w-full">
                    View Reports
                  </button>
                </div>
              </CardBody>
            </Card>
          </div>
        </div>
      </DashboardLayout>
    </>
  );
}