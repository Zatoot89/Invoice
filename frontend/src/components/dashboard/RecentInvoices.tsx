import { useState } from 'react';
import { 
  Button,
  Chip,
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  Avatar
} from '@nextui-org/react';
import { 
  EyeIcon, 
  PaperAirplaneIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline';
import { Invoice } from '@/types';

// Mock data - replace with actual API call
const mockInvoices: Partial<Invoice>[] = [
  {
    id: 1,
    invoice_number: 'INV-00000001',
    customer_name: 'Acme Corporation',
    total: 5500.00,
    status: 'sent',
    due_date: '2024-01-15T00:00:00Z',
    currency: 'USD',
  },
  {
    id: 2,
    invoice_number: 'INV-00000002',
    customer_name: 'Tech Solutions Inc',
    total: 3200.00,
    status: 'paid',
    due_date: '2024-01-10T00:00:00Z',
    currency: 'USD',
  },
  {
    id: 3,
    invoice_number: 'INV-00000003',
    customer_name: 'Global Enterprises',
    total: 8750.00,
    status: 'overdue',
    due_date: '2024-01-05T00:00:00Z',
    currency: 'USD',
  },
  {
    id: 4,
    invoice_number: 'INV-00000004',
    customer_name: 'Startup Inc',
    total: 1500.00,
    status: 'draft',
    due_date: '2024-01-20T00:00:00Z',
    currency: 'USD',
  },
  {
    id: 5,
    invoice_number: 'INV-00000005',
    customer_name: 'Digital Agency',
    total: 4250.00,
    status: 'sent',
    due_date: '2024-01-18T00:00:00Z',
    currency: 'USD',
  },
];

const statusColorMap = {
  draft: 'default',
  sent: 'primary',
  paid: 'success',
  overdue: 'danger',
  cancelled: 'default',
} as const;

const statusIcons = {
  draft: null,
  sent: PaperAirplaneIcon,
  paid: null,
  overdue: ExclamationTriangleIcon,
  cancelled: null,
};

export default function RecentInvoices() {
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set());

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }).format(new Date(dateString));
  };

  const getStatusChip = (status: string) => {
    const Icon = statusIcons[status as keyof typeof statusIcons];
    
    return (
      <Chip
        color={statusColorMap[status as keyof typeof statusColorMap]}
        variant="flat"
        size="sm"
        startContent={Icon && <Icon className="h-3 w-3" />}
      >
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Chip>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Recent Activity
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Your latest invoices and their status
          </p>
        </div>
        <Button size="sm" variant="light" href="/invoices">
          View All
        </Button>
      </div>

      <Table
        aria-label="Recent invoices table"
        selectionMode="multiple"
        selectedKeys={selectedKeys}
        onSelectionChange={(keys) => setSelectedKeys(keys as Set<string>)}
        classNames={{
          wrapper: "shadow-none border border-gray-200 dark:border-gray-700",
        }}
      >
        <TableHeader>
          <TableColumn>Invoice</TableColumn>
          <TableColumn>Customer</TableColumn>
          <TableColumn>Amount</TableColumn>
          <TableColumn>Status</TableColumn>
          <TableColumn>Due Date</TableColumn>
          <TableColumn>Actions</TableColumn>
        </TableHeader>
        <TableBody>
          {mockInvoices.map((invoice) => (
            <TableRow key={invoice.id}>
              <TableCell>
                <div className="flex flex-col">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {invoice.invoice_number}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    #{invoice.id}
                  </span>
                </div>
              </TableCell>
              <TableCell>
                <div className="flex items-center space-x-3">
                  <Avatar
                    size="sm"
                    name={invoice.customer_name}
                    className="bg-gradient-to-br from-blue-400 to-purple-500"
                  />
                  <span className="text-sm text-gray-900 dark:text-white">
                    {invoice.customer_name}
                  </span>
                </div>
              </TableCell>
              <TableCell>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {formatCurrency(invoice.total || 0, invoice.currency)}
                </span>
              </TableCell>
              <TableCell>
                {getStatusChip(invoice.status || 'draft')}
              </TableCell>
              <TableCell>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {formatDate(invoice.due_date || '')}
                </span>
              </TableCell>
              <TableCell>
                <div className="flex items-center space-x-2">
                  <Button
                    isIconOnly
                    size="sm"
                    variant="light"
                    href={`/invoices/${invoice.id}`}
                  >
                    <EyeIcon className="h-4 w-4" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}