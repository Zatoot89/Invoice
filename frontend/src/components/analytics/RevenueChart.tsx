import { useMemo } from 'react';
import {
  Card,
  CardBody,
  CardHeader,
  Select,
  SelectItem,
  Chip,
} from '@nextui-org/react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { formatCurrency, formatDate } from '@/lib/utils';

interface RevenueChartProps {
  data: any[];
  period: 'daily' | 'weekly' | 'monthly';
  chartType?: 'line' | 'area' | 'bar';
  showForecast?: boolean;
  className?: string;
}

export default function RevenueChart({
  data = [],
  period,
  chartType = 'area',
  showForecast = false,
  className
}: RevenueChartProps) {
  const chartData = useMemo(() => {
    return data.map(item => ({
      ...item,
      period: new Date(item.period).getTime(),
      formattedPeriod: formatDate(item.period, 
        period === 'daily' ? 'MMM dd' : 
        period === 'weekly' ? 'MMM dd' : 'MMM yyyy'
      )
    }));
  }, [data, period]);

  const maxRevenue = useMemo(() => {
    return Math.max(...chartData.map(item => item.revenue || 0));
  }, [chartData]);

  const totalRevenue = useMemo(() => {
    return chartData.reduce((sum, item) => sum + (item.revenue || 0), 0);
  }, [chartData]);

  const averageRevenue = useMemo(() => {
    return chartData.length > 0 ? totalRevenue / chartData.length : 0;
  }, [totalRevenue, chartData.length]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm font-semibold mb-2">
            {formatDate(new Date(label), period === 'daily' ? 'MMM dd, yyyy' : 'MMM yyyy')}
          </p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {`${entry.name}: ${formatCurrency(entry.value)}`}
            </p>
          ))}
          {payload[0]?.payload?.invoice_count && (
            <p className="text-xs text-gray-500 mt-1">
              {payload[0].payload.invoice_count} invoices
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  const renderChart = () => {
    const commonProps = {
      data: chartData,
      margin: { top: 5, right: 30, left: 20, bottom: 5 }
    };

    const commonAxisProps = {
      xAxis: {
        dataKey: 'period',
        tickFormatter: (value: number) => formatDate(new Date(value), 
          period === 'daily' ? 'MMM dd' : 'MMM yyyy'
        ),
        type: 'number' as const,
        scale: 'time' as const,
        domain: ['dataMin', 'dataMax']
      },
      yAxis: {
        tickFormatter: (value: number) => formatCurrency(value, { compact: true })
      }
    };

    switch (chartType) {
      case 'line':
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis {...commonAxisProps.xAxis} />
            <YAxis {...commonAxisProps.yAxis} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line
              type="monotone"
              dataKey="revenue"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2 }}
              name="Revenue"
            />
          </LineChart>
        );

      case 'bar':
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis {...commonAxisProps.xAxis} />
            <YAxis {...commonAxisProps.yAxis} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar
              dataKey="revenue"
              fill="#3b82f6"
              name="Revenue"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        );

      default: // area
        return (
          <AreaChart {...commonProps}>
            <defs>
              <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis {...commonAxisProps.xAxis} />
            <YAxis {...commonAxisProps.yAxis} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Area
              type="monotone"
              dataKey="revenue"
              stroke="#3b82f6"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorRevenue)"
              name="Revenue"
            />
          </AreaChart>
        );
    }
  };

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div>
          <h3 className="text-lg font-semibold">Revenue Trend</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {period.charAt(0).toUpperCase() + period.slice(1)} revenue analysis
          </p>
        </div>
        <div className="flex items-center space-x-4">
          {/* Summary chips */}
          <Chip variant="flat" color="primary" size="sm">
            Total: {formatCurrency(totalRevenue)}
          </Chip>
          <Chip variant="flat" color="secondary" size="sm">
            Avg: {formatCurrency(averageRevenue)}
          </Chip>
          <Chip variant="flat" color="success" size="sm">
            Peak: {formatCurrency(maxRevenue)}
          </Chip>
        </div>
      </CardHeader>
      
      <CardBody>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            {renderChart()}
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-64">
            <p className="text-gray-500">No revenue data available</p>
          </div>
        )}
      </CardBody>
    </Card>
  );
}

// Revenue comparison chart for multiple periods
export function RevenueComparisonChart({ 
  currentData = [], 
  previousData = [],
  period,
  className 
}: {
  currentData: any[];
  previousData: any[];
  period: 'daily' | 'weekly' | 'monthly';
  className?: string;
}) {
  const comparisonData = useMemo(() => {
    const maxLength = Math.max(currentData.length, previousData.length);
    const result = [];

    for (let i = 0; i < maxLength; i++) {
      const current = currentData[i] || { revenue: 0, period: null };
      const previous = previousData[i] || { revenue: 0, period: null };
      
      result.push({
        period: current.period || previous.period,
        currentRevenue: current.revenue || 0,
        previousRevenue: previous.revenue || 0,
        index: i
      });
    }

    return result;
  }, [currentData, previousData]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm font-semibold mb-2">
            Period {payload[0]?.payload?.index + 1}
          </p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {`${entry.name}: ${formatCurrency(entry.value)}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <Card className={className}>
      <CardHeader>
        <h3 className="text-lg font-semibold">Revenue Comparison</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Current vs Previous Period
        </p>
      </CardHeader>
      
      <CardBody>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={comparisonData}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis 
              dataKey="index" 
              tickFormatter={(value) => `Period ${value + 1}`}
            />
            <YAxis tickFormatter={(value) => formatCurrency(value, { compact: true })} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar
              dataKey="currentRevenue"
              fill="#3b82f6"
              name="Current Period"
              radius={[2, 2, 0, 0]}
            />
            <Bar
              dataKey="previousRevenue"
              fill="#94a3b8"
              name="Previous Period"
              radius={[2, 2, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </CardBody>
    </Card>
  );
}