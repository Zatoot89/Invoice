import { useMemo } from 'react';
import {
  Card,
  CardBody,
  CardHeader,
  Progress,
  Chip,
  Tabs,
  Tab,
  Divider,
} from '@nextui-org/react';
import {
  ComposedChart,
  Line,
  Bar,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import {
  TrendingUpIcon,
  TrendingDownIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  MinusIcon,
  BanknotesIcon,
  ChartBarIcon,
  ClockIcon,
  UserGroupIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';
import { formatCurrency, formatNumber, formatPercent } from '@/lib/utils';

interface AdvancedMetricsProps {
  dashboardData?: any;
  revenueData?: any;
  customerData?: any;
  performanceData?: any;
  className?: string;
}

export default function AdvancedMetrics({
  dashboardData,
  revenueData,
  customerData,
  performanceData,
  className
}: AdvancedMetricsProps) {
  // Combine all data for comprehensive analysis
  const combinedMetrics = useMemo(() => {
    const kpis = dashboardData?.kpis || {};
    const trends = dashboardData?.trends || {};
    
    return {
      revenue: {
        total: kpis.total_revenue || 0,
        trend: trends.revenue,
        outstanding: kpis.outstanding_amount || 0,
        growth_rate: revenueData?.growth_metrics?.growth_rate || 0
      },
      invoices: {
        total: kpis.total_invoices || 0,
        paid: kpis.paid_invoices || 0,
        overdue: kpis.overdue_invoices || 0,
        average_value: kpis.average_invoice_value || 0,
        trend: trends.invoices
      },
      customers: {
        active: kpis.active_customers || 0,
        new: kpis.new_customers || 0,
        retention_rate: customerData?.retention?.retention_rate || 0,
        ltv: customerData?.lifetime_value?.average_ltv || 0
      },
      performance: {
        payment_rate: kpis.payment_rate || 0,
        collection_rate: performanceData?.collection_efficiency?.collection_rate || 0,
        efficiency_score: performanceData?.collection_efficiency?.efficiency_score || 0,
        avg_payment_time: kpis.average_payment_time || 0
      }
    };
  }, [dashboardData, revenueData, customerData, performanceData]);

  // Radar chart data for performance overview
  const radarData = useMemo(() => {
    return [
      {
        subject: 'Revenue Growth',
        value: Math.min(Math.max(combinedMetrics.revenue.growth_rate + 50, 0), 100),
        fullMark: 100
      },
      {
        subject: 'Payment Rate',
        value: combinedMetrics.performance.payment_rate,
        fullMark: 100
      },
      {
        subject: 'Collection Efficiency',
        value: combinedMetrics.performance.efficiency_score,
        fullMark: 100
      },
      {
        subject: 'Customer Retention',
        value: combinedMetrics.customers.retention_rate,
        fullMark: 100
      },
      {
        subject: 'Invoice Processing',
        value: Math.max(100 - (combinedMetrics.performance.avg_payment_time * 2), 0),
        fullMark: 100
      }
    ];
  }, [combinedMetrics]);

  // Time series data for trend analysis
  const trendData = useMemo(() => {
    if (!revenueData?.time_series) return [];
    
    return revenueData.time_series.map((item: any, index: number) => ({
      period: new Date(item.period).toLocaleDateString('en-US', { month: 'short' }),
      revenue: item.revenue || 0,
      invoices: item.invoice_count || 0,
      avg_value: (item.revenue || 0) / Math.max(item.invoice_count || 1, 1)
    }));
  }, [revenueData]);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Key Performance Indicators Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Revenue Velocity"
          value={formatCurrency(combinedMetrics.revenue.total / Math.max(combinedMetrics.invoices.total, 1))}
          subtitle="Revenue per invoice"
          trend={combinedMetrics.revenue.trend}
          icon={<BanknotesIcon className="h-5 w-5" />}
          color="success"
        />
        
        <MetricCard
          title="Collection Efficiency"
          value={`${combinedMetrics.performance.collection_rate.toFixed(1)}%`}
          subtitle="Invoices collected"
          icon={<ChartBarIcon className="h-5 w-5" />}
          color="primary"
        />
        
        <MetricCard
          title="Cash Conversion"
          value={`${combinedMetrics.performance.avg_payment_time.toFixed(0)} days`}
          subtitle="Average payment time"
          icon={<ClockIcon className="h-5 w-5" />}
          color="warning"
        />
        
        <MetricCard
          title="Customer Health"
          value={`${combinedMetrics.customers.retention_rate.toFixed(1)}%`}
          subtitle="Retention rate"
          icon={<UserGroupIcon className="h-5 w-5" />}
          color="secondary"
        />
      </div>

      {/* Advanced Analytics Tabs */}
      <Tabs aria-label="Advanced Analytics" className="w-full">
        <Tab key="overview" title="Performance Overview">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Performance Radar Chart */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Performance Overview</h3>
              </CardHeader>
              <CardBody>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="subject" className="text-xs" />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} className="text-xs" />
                    <Radar
                      name="Performance"
                      dataKey="value"
                      stroke="#3b82f6"
                      fill="#3b82f6"
                      fillOpacity={0.3}
                      strokeWidth={2}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </CardBody>
            </Card>

            {/* Business Health Score */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Business Health Score</h3>
              </CardHeader>
              <CardBody className="space-y-4">
                <ScoreIndicator
                  label="Revenue Growth"
                  score={Math.min(Math.max(combinedMetrics.revenue.growth_rate + 50, 0), 100)}
                  target={75}
                />
                
                <ScoreIndicator
                  label="Payment Efficiency"
                  score={combinedMetrics.performance.payment_rate}
                  target={85}
                />
                
                <ScoreIndicator
                  label="Customer Retention"
                  score={combinedMetrics.customers.retention_rate}
                  target={80}
                />
                
                <ScoreIndicator
                  label="Cash Flow Health"
                  score={Math.max(100 - (combinedMetrics.performance.avg_payment_time * 2), 0)}
                  target={70}
                />
                
                <Divider />
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {Math.round(radarData.reduce((sum, item) => sum + item.value, 0) / radarData.length)}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Overall Health Score</p>
                </div>
              </CardBody>
            </Card>
          </div>
        </Tab>

        <Tab key="trends" title="Trend Analysis">
          {trendData.length > 0 ? (
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Revenue & Invoice Trends</h3>
              </CardHeader>
              <CardBody>
                <ResponsiveContainer width="100%" height={400}>
                  <ComposedChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                    <XAxis dataKey="period" />
                    <YAxis yAxisId="left" tickFormatter={(value) => formatCurrency(value, { compact: true })} />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip
                      formatter={(value, name) => {
                        if (name === 'Revenue') return [formatCurrency(value as number), name];
                        if (name === 'Average Value') return [formatCurrency(value as number), name];
                        return [formatNumber(value as number), name];
                      }}
                    />
                    <Legend />
                    
                    <Bar yAxisId="right" dataKey="invoices" fill="#94a3b8" name="Invoices" opacity={0.7} />
                    <Area
                      yAxisId="left"
                      type="monotone"
                      dataKey="revenue"
                      fill="#3b82f6"
                      fillOpacity={0.3}
                      stroke="#3b82f6"
                      name="Revenue"
                    />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="avg_value"
                      stroke="#10b981"
                      strokeWidth={3}
                      name="Average Value"
                      dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </CardBody>
            </Card>
          ) : (
            <Card>
              <CardBody className="text-center py-12">
                <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Trend Data</h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Trend analysis will appear once you have sufficient data points.
                </p>
              </CardBody>
            </Card>
          )}
        </Tab>

        <Tab key="forecasting" title="Forecasting">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Revenue Forecast</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Next Month</span>
                    <span className="font-semibold">
                      {formatCurrency(revenueData?.forecast?.forecast_revenue || 0)}
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Confidence Level</span>
                    <span className="font-semibold">
                      {((revenueData?.forecast?.confidence || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                  
                  <Progress 
                    value={(revenueData?.forecast?.confidence || 0) * 100}
                    color="primary"
                    className="w-full"
                  />
                  
                  <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg">
                    <p className="text-sm text-blue-800 dark:text-blue-200">
                      Based on historical trends and current performance metrics, 
                      revenue is projected to {combinedMetrics.revenue.growth_rate > 0 ? 'increase' : 'decrease'} 
                      by approximately {Math.abs(combinedMetrics.revenue.growth_rate).toFixed(1)}% next period.
                    </p>
                  </div>
                </div>
              </CardBody>
            </Card>

            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Performance Predictions</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  <PredictionItem
                    label="Collection Rate"
                    current={combinedMetrics.performance.collection_rate}
                    predicted={Math.min(combinedMetrics.performance.collection_rate + 2.5, 100)}
                    unit="%"
                  />
                  
                  <PredictionItem
                    label="Average Payment Time"
                    current={combinedMetrics.performance.avg_payment_time}
                    predicted={Math.max(combinedMetrics.performance.avg_payment_time - 1, 0)}
                    unit=" days"
                  />
                  
                  <PredictionItem
                    label="Customer Retention"
                    current={combinedMetrics.customers.retention_rate}
                    predicted={Math.min(combinedMetrics.customers.retention_rate + 1.5, 100)}
                    unit="%"
                  />
                </div>
              </CardBody>
            </Card>
          </div>
        </Tab>
      </Tabs>
    </div>
  );
}

// Metric Card Component
interface MetricCardProps {
  title: string;
  value: string;
  subtitle: string;
  trend?: {
    value: number;
    change: number;
    direction: 'up' | 'down' | 'neutral';
  };
  icon: React.ReactNode;
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
}

function MetricCard({ title, value, subtitle, trend, icon, color }: MetricCardProps) {
  const getTrendIcon = () => {
    if (!trend) return null;
    
    switch (trend.direction) {
      case 'up':
        return <TrendingUpIcon className="h-4 w-4 text-success-500" />;
      case 'down':
        return <TrendingDownIcon className="h-4 w-4 text-danger-500" />;
      default:
        return <MinusIcon className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTrendColor = () => {
    if (!trend) return 'default';
    return trend.direction === 'up' ? 'success' : trend.direction === 'down' ? 'danger' : 'default';
  };

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
              color={getTrendColor()}
              startContent={getTrendIcon()}
            >
              {trend.change > 0 ? '+' : ''}{trend.change.toFixed(1)}%
            </Chip>
          )}
        </div>
        
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1">
            {value}
          </p>
          <p className="text-xs text-gray-500">{subtitle}</p>
        </div>
      </CardBody>
    </Card>
  );
}

// Score Indicator Component
function ScoreIndicator({ label, score, target }: { label: string; score: number; target: number }) {
  const getColor = () => {
    if (score >= target) return 'success';
    if (score >= target * 0.8) return 'warning';
    return 'danger';
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>
        <div className="flex items-center space-x-2">
          <span className="text-sm font-semibold">{score.toFixed(0)}</span>
          {score >= target ? (
            <ArrowUpIcon className="h-3 w-3 text-success-500" />
          ) : (
            <ArrowDownIcon className="h-3 w-3 text-danger-500" />
          )}
        </div>
      </div>
      <Progress 
        value={score} 
        color={getColor()}
        className="w-full"
      />
      <div className="flex justify-between text-xs text-gray-500 mt-1">
        <span>0</span>
        <span>Target: {target}</span>
        <span>100</span>
      </div>
    </div>
  );
}

// Prediction Item Component
function PredictionItem({ 
  label, 
  current, 
  predicted, 
  unit 
}: { 
  label: string; 
  current: number; 
  predicted: number; 
  unit: string; 
}) {
  const change = predicted - current;
  const isPositive = change > 0;

  return (
    <div className="flex justify-between items-center">
      <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>
      <div className="flex items-center space-x-2">
        <span className="text-sm">{current.toFixed(1)}{unit}</span>
        <span className="text-xs text-gray-500">→</span>
        <span className={`text-sm font-semibold ${isPositive ? 'text-success-600' : 'text-danger-600'}`}>
          {predicted.toFixed(1)}{unit}
        </span>
        {isPositive ? (
          <ArrowUpIcon className="h-3 w-3 text-success-500" />
        ) : (
          <ArrowDownIcon className="h-3 w-3 text-danger-500" />
        )}
      </div>
    </div>
  );
}