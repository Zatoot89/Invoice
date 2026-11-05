import { ReactElement } from 'react';
import { Card, CardBody } from '@nextui-org/react';
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/outline';
import { clsx } from 'clsx';

interface StatsCardProps {
  title: string;
  value: string;
  change?: number;
  changeLabel?: string;
  icon: React.ComponentType<{ className?: string }>;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
}

const colorClasses = {
  primary: {
    iconBg: 'bg-blue-50 dark:bg-blue-900/20',
    iconColor: 'text-blue-600 dark:text-blue-400',
  },
  secondary: {
    iconBg: 'bg-gray-50 dark:bg-gray-900/20',
    iconColor: 'text-gray-600 dark:text-gray-400',
  },
  success: {
    iconBg: 'bg-green-50 dark:bg-green-900/20',
    iconColor: 'text-green-600 dark:text-green-400',
  },
  warning: {
    iconBg: 'bg-yellow-50 dark:bg-yellow-900/20',
    iconColor: 'text-yellow-600 dark:text-yellow-400',
  },
  danger: {
    iconBg: 'bg-red-50 dark:bg-red-900/20',
    iconColor: 'text-red-600 dark:text-red-400',
  },
};

export default function StatsCard({
  title,
  value,
  change,
  changeLabel,
  icon: Icon,
  color = 'primary',
}: StatsCardProps) {
  const isPositive = change && change > 0;
  const isNegative = change && change < 0;
  const colorClass = colorClasses[color];

  return (
    <Card className="shadow-soft hover:shadow-medium transition-shadow duration-200">
      <CardBody className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {title}
            </p>
            <p className="mt-1 text-3xl font-bold text-gray-900 dark:text-white">
              {value}
            </p>
            
            {change !== undefined && changeLabel && (
              <div className="mt-2 flex items-center">
                {isPositive && (
                  <ArrowUpIcon className="mr-1 h-4 w-4 text-green-500" />
                )}
                {isNegative && (
                  <ArrowDownIcon className="mr-1 h-4 w-4 text-red-500" />
                )}
                <span
                  className={clsx(
                    'text-sm font-medium',
                    isPositive && 'text-green-600 dark:text-green-400',
                    isNegative && 'text-red-600 dark:text-red-400',
                    !isPositive && !isNegative && 'text-gray-600 dark:text-gray-400'
                  )}
                >
                  {changeLabel}
                </span>
              </div>
            )}
          </div>
          
          <div
            className={clsx(
              'flex h-12 w-12 items-center justify-center rounded-lg',
              colorClass.iconBg
            )}
          >
            <Icon className={clsx('h-6 w-6', colorClass.iconColor)} />
          </div>
        </div>
      </CardBody>
    </Card>
  );
}