import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Button,
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  Checkbox,
  Input,
  Select,
  SelectItem,
  Tabs,
  Tab,
  Chip,
  Pagination,
  useDisclosure
} from '@nextui-org/react';
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  DocumentArrowDownIcon,
  DocumentArrowUpIcon
} from '@heroicons/react/24/outline';
import BulkActions from './BulkActions';
import CSVImportWizard from './CSVImportWizard';
import { toast } from 'react-hot-toast';

interface Invoice {
  id: number;
  invoice_number: string;
  customer_name: string;
  status: string;
  total: number;
  due_date: string;
  created_at: string;
}

interface Customer {
  id: number;
  name: string;
  email: string;
  company: string;
  total_invoices: number;
  total_amount: number;
  is_active: boolean;
  created_at: string;
}

interface BulkOperationsDashboardProps {
  defaultTab?: 'invoices' | 'customers';
}

export default function BulkOperationsDashboard({ defaultTab = 'invoices' }: BulkOperationsDashboardProps) {
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [selectedItems, setSelectedItems] = useState<number[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  
  // Data
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [totalPages, setTotalPages] = useState(1);
  
  const importWizard = useDisclosure();
  
  const itemsPerPage = 20;

  useEffect(() => {
    fetchData();
  }, [activeTab, currentPage, searchQuery, statusFilter]);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const endpoint = activeTab === 'invoices' ? '/api/v1/invoices' : '/api/v1/customers';
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: itemsPerPage.toString(),
        ...(searchQuery && { search: searchQuery }),
        ...(statusFilter && { status: statusFilter })
      });

      const response = await fetch(`${endpoint}?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch data');

      const data = await response.json();
      
      if (activeTab === 'invoices') {
        setInvoices(data.items || []);
      } else {
        setCustomers(data.items || []);
      }
      
      setTotalPages(Math.ceil((data.total || 0) / itemsPerPage));
    } catch (error) {
      toast.error(`Failed to fetch ${activeTab}: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectItem = (id: number, checked: boolean) => {
    if (checked) {
      setSelectedItems([...selectedItems, id]);
    } else {
      setSelectedItems(selectedItems.filter(item => item !== id));
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const allIds = activeTab === 'invoices' 
        ? invoices.map(invoice => invoice.id)
        : customers.map(customer => customer.id);
      setSelectedItems(allIds);
    } else {
      setSelectedItems([]);
    }
  };

  const handleActionComplete = () => {
    setSelectedItems([]);
    fetchData();
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'paid':
        return 'success';
      case 'sent':
        return 'primary';
      case 'overdue':
        return 'danger';
      case 'draft':
        return 'default';
      default:
        return 'default';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const renderInvoicesTable = () => (
    <Table
      aria-label="Invoices table"
      selectionMode="multiple"
      selectedKeys={new Set(selectedItems.map(String))}
      onSelectionChange={(keys) => {
        if (keys === "all") {
          handleSelectAll(true);
        } else {
          setSelectedItems(Array.from(keys).map(Number));
        }
      }}
    >
      <TableHeader>
        <TableColumn>Invoice #</TableColumn>
        <TableColumn>Customer</TableColumn>
        <TableColumn>Status</TableColumn>
        <TableColumn>Amount</TableColumn>
        <TableColumn>Due Date</TableColumn>
        <TableColumn>Created</TableColumn>
      </TableHeader>
      <TableBody
        isLoading={isLoading}
        emptyContent="No invoices found"
      >
        {invoices.map((invoice) => (
          <TableRow key={invoice.id}>
            <TableCell className="font-mono">{invoice.invoice_number}</TableCell>
            <TableCell>{invoice.customer_name}</TableCell>
            <TableCell>
              <Chip
                color={getStatusColor(invoice.status)}
                size="sm"
                variant="flat"
              >
                {invoice.status}
              </Chip>
            </TableCell>
            <TableCell className="font-mono">{formatCurrency(invoice.total)}</TableCell>
            <TableCell>{formatDate(invoice.due_date)}</TableCell>
            <TableCell>{formatDate(invoice.created_at)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );

  const renderCustomersTable = () => (
    <Table
      aria-label="Customers table"
      selectionMode="multiple"
      selectedKeys={new Set(selectedItems.map(String))}
      onSelectionChange={(keys) => {
        if (keys === "all") {
          handleSelectAll(true);
        } else {
          setSelectedItems(Array.from(keys).map(Number));
        }
      }}
    >
      <TableHeader>
        <TableColumn>Name</TableColumn>
        <TableColumn>Email</TableColumn>
        <TableColumn>Company</TableColumn>
        <TableColumn>Invoices</TableColumn>
        <TableColumn>Total Amount</TableColumn>
        <TableColumn>Status</TableColumn>
        <TableColumn>Created</TableColumn>
      </TableHeader>
      <TableBody
        isLoading={isLoading}
        emptyContent="No customers found"
      >
        {customers.map((customer) => (
          <TableRow key={customer.id}>
            <TableCell>{customer.name}</TableCell>
            <TableCell>{customer.email}</TableCell>
            <TableCell>{customer.company || '-'}</TableCell>
            <TableCell>{customer.total_invoices}</TableCell>
            <TableCell className="font-mono">{formatCurrency(customer.total_amount)}</TableCell>
            <TableCell>
              <Chip
                color={customer.is_active ? 'success' : 'default'}
                size="sm"
                variant="flat"
              >
                {customer.is_active ? 'Active' : 'Inactive'}
              </Chip>
            </TableCell>
            <TableCell>{formatDate(customer.created_at)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <h2 className="text-2xl font-bold">Bulk Operations</h2>
            <div className="flex gap-2">
              <Button
                startContent={<DocumentArrowDownIcon className="h-4 w-4" />}
                variant="bordered"
                size="sm"
              >
                Export All
              </Button>
              {activeTab === 'customers' && (
                <Button
                  startContent={<DocumentArrowUpIcon className="h-4 w-4" />}
                  color="primary"
                  size="sm"
                  onPress={importWizard.onOpen}
                >
                  Import
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      <Tabs
        selectedKey={activeTab}
        onSelectionChange={(key) => {
          setActiveTab(key as string);
          setSelectedItems([]);
          setCurrentPage(1);
        }}
        className="w-full"
      >
        <Tab key="invoices" title="Invoices">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between w-full">
                <div className="flex gap-4 items-center">
                  <Input
                    placeholder="Search invoices..."
                    startContent={<MagnifyingGlassIcon className="h-4 w-4" />}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="max-w-xs"
                  />
                  <Select
                    placeholder="Filter by status"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="max-w-xs"
                    startContent={<FunnelIcon className="h-4 w-4" />}
                  >
                    <SelectItem key="" value="">All Statuses</SelectItem>
                    <SelectItem key="draft" value="draft">Draft</SelectItem>
                    <SelectItem key="sent" value="sent">Sent</SelectItem>
                    <SelectItem key="paid" value="paid">Paid</SelectItem>
                    <SelectItem key="overdue" value="overdue">Overdue</SelectItem>
                  </Select>
                </div>
                
                <BulkActions
                  selectedItems={selectedItems}
                  itemType="invoices"
                  onActionComplete={handleActionComplete}
                />
              </div>
            </CardHeader>
            <CardBody>
              {selectedItems.length > 0 && (
                <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-700">
                    {selectedItems.length} invoice{selectedItems.length !== 1 ? 's' : ''} selected
                  </p>
                </div>
              )}
              
              {renderInvoicesTable()}
              
              {totalPages > 1 && (
                <div className="flex justify-center mt-4">
                  <Pagination
                    total={totalPages}
                    page={currentPage}
                    onChange={setCurrentPage}
                  />
                </div>
              )}
            </CardBody>
          </Card>
        </Tab>

        <Tab key="customers" title="Customers">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between w-full">
                <div className="flex gap-4 items-center">
                  <Input
                    placeholder="Search customers..."
                    startContent={<MagnifyingGlassIcon className="h-4 w-4" />}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="max-w-xs"
                  />
                  <Select
                    placeholder="Filter by status"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="max-w-xs"
                    startContent={<FunnelIcon className="h-4 w-4" />}
                  >
                    <SelectItem key="" value="">All Customers</SelectItem>
                    <SelectItem key="active" value="active">Active</SelectItem>
                    <SelectItem key="inactive" value="inactive">Inactive</SelectItem>
                  </Select>
                </div>
                
                <BulkActions
                  selectedItems={selectedItems}
                  itemType="customers"
                  onActionComplete={handleActionComplete}
                />
              </div>
            </CardHeader>
            <CardBody>
              {selectedItems.length > 0 && (
                <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-700">
                    {selectedItems.length} customer{selectedItems.length !== 1 ? 's' : ''} selected
                  </p>
                </div>
              )}
              
              {renderCustomersTable()}
              
              {totalPages > 1 && (
                <div className="flex justify-center mt-4">
                  <Pagination
                    total={totalPages}
                    page={currentPage}
                    onChange={setCurrentPage}
                  />
                </div>
              )}
            </CardBody>
          </Card>
        </Tab>
      </Tabs>

      {/* Import Wizard */}
      <CSVImportWizard
        isOpen={importWizard.isOpen}
        onOpenChange={importWizard.onOpenChange}
        importType="customers"
        onImportComplete={handleActionComplete}
      />
    </div>
  );
}