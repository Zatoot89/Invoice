import { useState, useEffect } from 'react';
import {
  Card,
  CardBody,
  CardHeader,
  Button,
  Select,
  SelectItem,
  Tabs,
  Tab,
  Spinner,
  Chip,
  Progress,
} from '@nextui-org/react';
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  UserGroupIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { formatCurrency, formatNumber, formatDate } from '@/lib/utils';
import { useAnalytics } from '@/hooks/useAnalytics';
import AdvancedMetrics from './AdvancedMetrics';

interface AnalyticsDashboardProps {
  className?: string;
}

const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export default function AnalyticsDashboard({ className }: AnalyticsDashboardProps) {
  const [activeTab, setActiveTab] = useState('overview');
  const [dateRange, setDateRange] = useState('30');
  const [period, setPeriod] = useState('monthly');
  
  const {
    dashboardData,
    revenueData,
    customerData,
    performanceData,
    loading,
    error,
    refreshData
  } = useAnalytics({
    dateRange: parseInt(dateRange),
    period
  });

  const handleDateRangeChange = (value: string) => {
    setDateRange(value);
    refreshData({ dateRange: parseInt(value) });
  };

  const handlePeriodChange = (value: string) => {
    setPeriod(value);
    refreshData({ period: value });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" label="Loading analytics..." />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-danger-200">
        <CardBody className="text-center py-8">
          <p className="text-danger-600 mb-4">Failed to load analytics data</p>
          <Button color="primary" variant="flat" onPress={() => refreshData()}>
            Try Again
          </Button>
        </CardBody>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Analytics Dashboard
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Comprehensive business insights and performance metrics
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Select
            size="sm"
            label="Date Range"
            selectedKeys={[dateRange]}
            onSelectionChange={(keys) => handleDateRangeChange(Array.from(keys)[0] as string)}
            className="w-32"
          >
            <SelectItem key="7" value="7">Last 7 days</SelectItem>
            <SelectItem key="30" value="30">Last 30 days</SelectItem>
            <SelectItem key="90" value="90">Last 90 days</SelectItem>
            <SelectItem key="365" value="365">Last year</SelectItem>
          </Select>
          
          <Select
            size="sm"
            label="Period"
            selectedKeys={[period]}
            onSelectionChange={(keys) => handlePeriodChange(Array.from(keys)[0] as string)}
            className="w-32"
          >
            <SelectItem key="daily" value="daily">Daily</SelectItem>
            <SelectItem key="weekly" value="weekly">Weekly</SelectItem>
            <SelectItem key="monthly" value="monthly">Monthly</SelectItem>
          </Select>
        </div>
      </div>

      {/* Tabs */}
      <Tabs 
        aria-label="Analytics tabs" 
        selectedKey={activeTab}
        onSelectionChange={(key) => setActiveTab(key as string)}
        className="w-full"
      >
        <Tab key="overview" title="Overview">
          <OverviewTab data={dashboardData} />
        </Tab>
        <Tab key="revenue" title="Revenue">
          <RevenueTab data={revenueData} />
        </Tab>
        <Tab key="customers" title="Customers">
          <CustomerTab data={customerData} />
        </Tab>
        <Tab key="performance" title="Performance">
          <PerformanceTab data={performanceData} />
        </Tab>
        <Tab key="advanced" title="Advanced Metrics">
          <AdvancedMetrics
            dashboardData={dashboardData}
            revenueData={revenueData}
            customerData={customerData}
            performanceData={performanceData}
          />
        </Tab>
      </Tabs>
    </div>
  );
}

// Overview Tab Component
function OverviewTab({ data }: { data: any }) {
  if (!data) return <div>No data available</div>;

  const { kpis, trends, status_breakdown } = data;

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Revenue"
          value={formatCurrency(kpis?.total_revenue || 0)}
          trend={trends?.revenue}
          icon={<CurrencyDollarIcon className="h-6 w-6" />}
          color="success"
        />
        <KPICard
          title="Outstanding Amount"
          value={formatCurrency(kpis?.outstanding_amount || 0)}
          icon={<DocumentTextIcon className="h-6 w-6" />}
          color="warning"
        />
        <KPICard
          title="Total Invoices"
          value={formatNumber(kpis?.total_invoices || 0)}
          trend={trends?.invoices}
          icon={<ChartBarIcon className="h-6 w-6" />}
          color="primary"
        />
        <KPICard
          title="Active Customers"
          value={formatNumber(kpis?.active_customers || 0)}
          icon={<UserGroupIcon className="h-6 w-6" />}
          color="secondary"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Invoice Status Distribution */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Invoice Status Distribution</h3>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={Object.entries(status_breakdown || {}).map(([status, count]) => ({
                    name: status.charAt(0).toUpperCase() + status.slice(1),
                    value: count,
                  }))}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {Object.keys(status_breakdown || {}).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        {/* Key Metrics Summary */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Key Metrics</h3>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Payment Rate</span>
              <div className="flex items-center space-x-2">
                <Progress 
                  value={kpis?.payment_rate || 0} 
                  className="w-20" 
                  color="success"
                />
                <span className="text-sm font-semibold">
                  {(kpis?.payment_rate || 0).toFixed(1)}%
                </span>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Average Invoice Value</span>
              <span className="text-sm font-semibold">
                {formatCurrency(kpis?.average_invoice_value || 0)}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Average Payment Time</span>
              <span className="text-sm font-semibold">
                {(kpis?.average_payment_time || 0).toFixed(0)} days
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">New Customers</span>
              <span className="text-sm font-semibold">
                +{kpis?.new_customers || 0}
              </span>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

// Revenue Tab Component
function RevenueTab({ data }: { data: any }) {
  if (!data) return <div>No data available</div>;

  const { time_series, forecast } = data;

  return (
    <div className="space-y-6">
      {/* Revenue Trend Chart */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">Revenue Trend</h3>
        </CardHeader>
        <CardBody>
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={time_series || []}>
              <defs>
                <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="period" 
                tickFormatter={(value) => formatDate(value, 'MMM dd')}
              />
              <YAxis tickFormatter={(value) => formatCurrency(value, { compact: true })} />
              <Tooltip 
                formatter={(value) => [formatCurrency(value as number), 'Revenue']}
                labelFormatter={(label) => formatDate(label)}
              />
              <Area
                type="monotone"
                dataKey="revenue"
                stroke="#3b82f6"
                fillOpacity={1}
                fill="url(#colorRevenue)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardBody>
      </Card>

      {/* Revenue Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardBody>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Revenue</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(time_series?.reduce((sum: number, item: any) => sum + item.revenue, 0) || 0)}
                </p>
              </div>
              <TrendingUpIcon className="h-8 w-8 text-green-500" />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Average per Period</p>
                <p className="text-2xl font-bold text-blue-600">
                  {formatCurrency(
                    (time_series?.reduce((sum: number, item: any) => sum + item.revenue, 0) || 0) / 
                    (time_series?.length || 1)
                  )}
                </p>
              </div>
              <ChartBarIcon className="h-8 w-8 text-blue-500" />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Forecast Confidence</p>
                <p className="text-2xl font-bold text-purple-600">
                  {((forecast?.confidence || 0) * 100).toFixed(0)}%
                </p>
              </div>
              <TrendingUpIcon className="h-8 w-8 text-purple-500" />
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

// Customer Tab Component
function CustomerTab({ data }: { data: any }) {
  if (!data) return <div>No data available</div>;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">Customer Analytics</h3>
        </CardHeader>
        <CardBody>
          <p className="text-gray-600 dark:text-gray-400">
            Customer analytics coming soon with retention rates, lifetime value, and acquisition costs.
          </p>
        </CardBody>
      </Card>
    </div>
  );
}

// Performance Tab Component
function PerformanceTab({ data }: { data: any }) {
  if (!data) return <div>No data available</div>;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">Performance Metrics</h3>
        </CardHeader>
        <CardBody>
          <p className="text-gray-600 dark:text-gray-400">
            Performance analytics coming soon with collection efficiency, cash flow analysis, and performance scoring.
          </p>
        </CardBody>
      </Card>
    </div>
  );
}

// KPI Card Component
interface KPICardProps {
  title: string;
  value: string | number;
  trend?: {
    value: number;
    change: number;
    direction: 'up' | 'down' | 'neutral';
  };
  icon: React.ReactNode;
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
}

function KPICard({ title, value, trend, icon, color }: KPICardProps) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardBody>
        <div className="flex items-center justify-between mb-3">
          <div className={`p-2 rounded-lg bg-${color}-100 dark:bg-${color}-900/30`}>
            <div className={`text-${color}-600 dark:text-${color}-400`}>
              {icon}
            </div>
          </div>
          {trend && (
            <Chip
              size="sm"
              variant="flat"
              color={trend.direction === 'up' ? 'success' : trend.direction === 'down' ? 'danger' : 'default'}
              startContent={
                trend.direction === 'up' ? (
                  <ArrowUpIcon className="h-3 w-3" />
                ) : trend.direction === 'down' ? (
                  <ArrowDownIcon className="h-3 w-3" />
                ) : null
              }
            >
              {trend.change > 0 ? '+' : ''}{trend.change.toFixed(1)}%
            </Chip>
          )}
        </div>
        
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {value}
          </p>
        </div>
      </CardBody>
    </Card>
  );
}