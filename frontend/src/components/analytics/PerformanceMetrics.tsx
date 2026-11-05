import { useMemo } from 'react';
import {
  Card,
  CardBody,
  CardHeader,
  Progress,
  Chip,
  Divider,
} from '@nextui-org/react';
import {
  RadialBarChart,
  RadialBar,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CurrencyDollarIcon,
  TrendingUpIcon,
  TrendingDownIcon,
} from '@heroicons/react/24/outline';
import { formatCurrency, formatNumber, formatPercent } from '@/lib/utils';

interface PerformanceMetricsProps {
  data: {
    collection_efficiency?: {
      efficiency_score: number;
      collection_rate: number;
    };
    invoice_processing?: {
      avg_processing_time: number;
      bottlenecks: string[];
    };
    cash_flow?: {
      cash_flow_timeline: any[];
      projected_cash_flow: any[];
    };
    aging_analysis?: {
      aging_buckets: {
        '0-30': number;
        '31-60': number;
        '61-90': number;
        '90+': number;
      };
    };
    performance_score?: {
      score: number;
      grade: string;
      improvement_areas: string[];
    };
  };
  className?: string;
}

const COLORS = ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function PerformanceMetrics({ data, className }: PerformanceMetricsProps) {
  const agingChartData = useMemo(() => {
    if (!data.aging_analysis) return [];
    
    return Object.entries(data.aging_analysis.aging_buckets).map(([range, value], index) => ({
      name: range === '90+' ? '90+ days' : `${range} days`,
      value: value || 0,
      color: COLORS[index % COLORS.length]
    }));
  }, [data.aging_analysis]);

  const performanceScore = data.performance_score?.score || 0;
  const collectionRate = data.collection_efficiency?.collection_rate || 0;
  const efficiencyScore = data.collection_efficiency?.efficiency_score || 0;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Performance Score Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <PerformanceScoreCard
          title="Overall Performance"
          score={performanceScore}
          grade={data.performance_score?.grade || 'N/A'}
          subtitle="Business performance score"
        />
        
        <PerformanceScoreCard
          title="Collection Efficiency"
          score={efficiencyScore}
          subtitle="Payment collection efficiency"
        />
        
        <PerformanceScoreCard
          title="Collection Rate"
          score={collectionRate}
          subtitle="Percentage of invoices collected"
        />
      </div>

      {/* Detailed Metrics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Invoice Aging Analysis */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Invoice Aging Analysis</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Outstanding invoices by age
                </p>
              </div>
              <ClockIcon className="h-6 w-6 text-gray-500" />
            </div>
          </CardHeader>
          
          <CardBody>
            {agingChartData.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={agingChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => 
                        percent > 5 ? `${name} ${(percent * 100).toFixed(0)}%` : ''
                      }
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {agingChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      formatter={(value: number) => [formatNumber(value), 'Invoices']}
                    />
                  </PieChart>
                </ResponsiveContainer>
                
                <div className="mt-4 space-y-2">
                  {agingChartData.map((item, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <div className="flex items-center space-x-2">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: item.color }}
                        />
                        <span>{item.name}</span>
                      </div>
                      <span className="font-semibold">{formatNumber(item.value)}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="flex items-center justify-center h-64">
                <p className="text-gray-500">No aging data available</p>
              </div>
            )}
          </CardBody>
        </Card>

        {/* Processing Metrics */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Processing Metrics</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Invoice processing efficiency
                </p>
              </div>
              <TrendingUpIcon className="h-6 w-6 text-gray-500" />
            </div>
          </CardHeader>
          
          <CardBody className="space-y-6">
            {/* Processing Time */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Average Processing Time
                </span>
                <span className="text-lg font-bold text-blue-600">
                  {(data.invoice_processing?.avg_processing_time || 0).toFixed(1)} days
                </span>
              </div>
              <Progress 
                value={Math.min((data.invoice_processing?.avg_processing_time || 0) / 7 * 100, 100)}
                color={
                  (data.invoice_processing?.avg_processing_time || 0) < 2 ? 'success' :
                  (data.invoice_processing?.avg_processing_time || 0) < 5 ? 'warning' : 'danger'
                }
                className="w-full"
              />
            </div>

            <Divider />

            {/* Bottlenecks */}
            <div>
              <h4 className="text-sm font-semibold mb-3">Process Bottlenecks</h4>
              <div className="space-y-2">
                {data.invoice_processing?.bottlenecks?.length ? (
                  data.invoice_processing.bottlenecks.map((bottleneck, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <ExclamationTriangleIcon className="h-4 w-4 text-warning-500" />
                      <span className="text-sm">{bottleneck}</span>
                    </div>
                  ))
                ) : (
                  <div className="flex items-center space-x-2 text-success-600">
                    <CheckCircleIcon className="h-4 w-4" />
                    <span className="text-sm">No bottlenecks identified</span>
                  </div>
                )}
              </div>
            </div>

            <Divider />

            {/* Improvement Areas */}
            {data.performance_score?.improvement_areas?.length && (
              <div>
                <h4 className="text-sm font-semibold mb-3">Improvement Areas</h4>
                <div className="flex flex-wrap gap-2">
                  {data.performance_score.improvement_areas.map((area, index) => (
                    <Chip key={index} variant="flat" color="warning" size="sm">
                      {area}
                    </Chip>
                  ))}
                </div>
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Cash Flow Timeline */}
      {data.cash_flow?.cash_flow_timeline?.length && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Cash Flow Analysis</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Historical and projected cash flow
                </p>
              </div>
              <CurrencyDollarIcon className="h-6 w-6 text-gray-500" />
            </div>
          </CardHeader>
          
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.cash_flow.cash_flow_timeline}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis 
                  dataKey="period" 
                  tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short' })}
                />
                <YAxis tickFormatter={(value) => formatCurrency(value, { compact: true })} />
                <Tooltip 
                  formatter={(value: number) => [formatCurrency(value), 'Cash Flow']}
                  labelFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <Bar
                  dataKey="amount"
                  fill="#3b82f6"
                  radius={[2, 2, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      )}
    </div>
  );
}

// Performance Score Card Component
interface PerformanceScoreCardProps {
  title: string;
  score: number;
  grade?: string;
  subtitle: string;
}

function PerformanceScoreCard({ title, score, grade, subtitle }: PerformanceScoreCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'success';
    if (score >= 70) return 'warning';
    return 'danger';
  };

  const getGradeColor = (grade?: string) => {
    switch (grade) {
      case 'A': return 'success';
      case 'B': return 'primary';
      case 'C': return 'warning';
      case 'D':
      case 'F': return 'danger';
      default: return 'default';
    }
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardBody className="text-center">
        <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
          {title}
        </h3>
        
        <div className="mb-4">
          <ResponsiveContainer width="100%" height={120}>
            <RadialBarChart
              cx="50%"
              cy="50%"
              innerRadius="60%"
              outerRadius="90%"
              data={[{ score, fill: getScoreColor(score) === 'success' ? '#10b981' : getScoreColor(score) === 'warning' ? '#f59e0b' : '#ef4444' }]}
            >
              <RadialBar
                dataKey="score"
                cornerRadius={10}
                fill="#8884d8"
              />
            </RadialBarChart>
          </ResponsiveContainer>
        </div>
        
        <div className="space-y-2">
          <div className="flex items-center justify-center space-x-2">
            <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {score.toFixed(0)}%
            </span>
            {grade && (
              <Chip
                variant="flat"
                color={getGradeColor(grade)}
                size="sm"
              >
                Grade {grade}
              </Chip>
            )}
          </div>
          
          <p className="text-xs text-gray-500">{subtitle}</p>
        </div>
      </CardBody>
    </Card>
  );
}

// Export additional performance widgets
export { PerformanceScoreCard };