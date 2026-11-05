import { useState } from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import {
  Card,
  CardBody,
  Button,
  Tabs,
  Tab,
  Select,
  SelectItem,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useDisclosure,
} from '@nextui-org/react';
import {
  ArrowDownTrayIcon,
  Cog6ToothIcon,
  PresentationChartLineIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '@/contexts/AuthContext';
import Layout from '@/components/layout/Layout';
import AnalyticsDashboard from '@/components/analytics/AnalyticsDashboard';
import RevenueChart, { RevenueComparisonChart } from '@/components/analytics/RevenueChart';
import PerformanceMetrics from '@/components/analytics/PerformanceMetrics';
import { useAnalytics, useRealTimeAnalytics } from '@/hooks/useAnalytics';
import toast from 'react-hot-toast';

const AnalyticsPage: NextPage = () => {
  const { user } = useAuth();
  const [activeView, setActiveView] = useState('dashboard');
  const [exportFormat, setExportFormat] = useState('json');
  const { isOpen: isExportOpen, onOpen: onExportOpen, onClose: onExportClose } = useDisclosure();
  const { isOpen: isSettingsOpen, onOpen: onSettingsOpen, onClose: onSettingsClose } = useDisclosure();

  const {
    dashboardData,
    revenueData,
    performanceData,
    loading,
    error,
    exportData,
    createAlert
  } = useAnalytics({
    dateRange: 30,
    period: 'monthly',
    autoRefresh: true
  });

  const {
    data: realTimeData,
    loading: realTimeLoading
  } = useRealTimeAnalytics();

  const handleExport = async () => {
    try {
      const data = await exportData(
        activeView as 'dashboard' | 'revenue' | 'customers' | 'performance',
        exportFormat as 'json' | 'csv' | 'pdf'
      );
      
      if (data && exportFormat === 'json') {
        // Download JSON file
        const blob = new Blob([JSON.stringify(data, null, 2)], { 
          type: 'application/json' 
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analytics-${activeView}-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
      
      toast.success('Analytics data exported successfully');
      onExportClose();
    } catch (error) {
      toast.error('Failed to export analytics data');
    }
  };

  const handleCreateAlert = async () => {
    try {
      await createAlert('revenue', 'below', 1000, 'email');
      toast.success('Analytics alert created');
      onSettingsClose();
    } catch (error) {
      toast.error('Failed to create alert');
    }
  };

  if (!user) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <p>Please log in to view analytics</p>
        </div>
      </Layout>
    );
  }

  return (
    <>
      <Head>
        <title>Analytics - InvoiceFlow Pro</title>
        <meta name="description" content="Comprehensive business analytics and insights" />
      </Head>

      <Layout>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                Business Analytics
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Comprehensive insights into your business performance
              </p>
            </div>

            <div className="flex items-center space-x-3">
              <Button
                variant="flat"
                startContent={<ArrowDownTrayIcon className="h-4 w-4" />}
                onPress={onExportOpen}
              >
                Export
              </Button>
              <Button
                variant="flat"
                startContent={<Cog6ToothIcon className="h-4 w-4" />}
                onPress={onSettingsOpen}
              >
                Settings
              </Button>
            </div>
          </div>

          {/* Real-time Stats Bar */}
          {realTimeData && !realTimeLoading && (
            <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950">
              <CardBody>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <PresentationChartLineIcon className="h-5 w-5 text-blue-600" />
                    <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                      Real-time Metrics
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
                    <div className="text-center">
                      <p className="text-xs text-blue-600 dark:text-blue-400">Today's Revenue</p>
                      <p className="text-sm font-bold text-blue-900 dark:text-blue-100">
                        ${realTimeData.today?.revenue?.toLocaleString() || '0'}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-blue-600 dark:text-blue-400">Invoices Sent</p>
                      <p className="text-sm font-bold text-blue-900 dark:text-blue-100">
                        {realTimeData.today?.invoices_sent || 0}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-blue-600 dark:text-blue-400">Payments Received</p>
                      <p className="text-sm font-bold text-blue-900 dark:text-blue-100">
                        {realTimeData.today?.payments_received || 0}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-blue-600 dark:text-blue-400">Active Sessions</p>
                      <p className="text-sm font-bold text-blue-900 dark:text-blue-100">
                        {realTimeData.active_sessions || 0}
                      </p>
                    </div>
                  </div>
                </div>
              </CardBody>
            </Card>
          )}

          {/* Main Analytics Tabs */}
          <Tabs 
            selectedKey={activeView}
            onSelectionChange={(key) => setActiveView(key as string)}
            className="w-full"
            size="lg"
          >
            <Tab key="dashboard" title="Overview">
              <AnalyticsDashboard />
            </Tab>

            <Tab key="revenue" title="Revenue Analytics">
              <div className="space-y-6">
                {revenueData && (
                  <>
                    <RevenueChart
                      data={revenueData.time_series || []}
                      period="monthly"
                      chartType="area"
                    />
                    
                    {/* Additional revenue metrics can be added here */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <Card>
                        <CardBody>
                          <h3 className="text-lg font-semibold mb-4">Revenue Growth</h3>
                          <p className="text-gray-600 dark:text-gray-400">
                            Growth rate: {revenueData.growth_metrics?.growth_rate || 0}%
                          </p>
                          <p className="text-gray-600 dark:text-gray-400">
                            Momentum: {revenueData.growth_metrics?.momentum || 'steady'}
                          </p>
                        </CardBody>
                      </Card>

                      <Card>
                        <CardBody>
                          <h3 className="text-lg font-semibold mb-4">Forecast</h3>
                          <p className="text-gray-600 dark:text-gray-400">
                            Projected revenue: ${revenueData.forecast?.forecast_revenue || 0}
                          </p>
                          <p className="text-gray-600 dark:text-gray-400">
                            Confidence: {((revenueData.forecast?.confidence || 0) * 100).toFixed(0)}%
                          </p>
                        </CardBody>
                      </Card>
                    </div>
                  </>
                )}
              </div>
            </Tab>

            <Tab key="customers" title="Customer Analytics">
              <Card>
                <CardBody className="text-center py-12">
                  <h3 className="text-lg font-semibold mb-2">Customer Analytics</h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-4">
                    Detailed customer insights coming soon
                  </p>
                  <p className="text-sm text-gray-500">
                    This will include customer acquisition, retention, lifetime value, 
                    and behavior analysis.
                  </p>
                </CardBody>
              </Card>
            </Tab>

            <Tab key="performance" title="Performance">
              {performanceData ? (
                <PerformanceMetrics data={performanceData} />
              ) : (
                <Card>
                  <CardBody className="text-center py-12">
                    <h3 className="text-lg font-semibold mb-2">Performance Metrics</h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      Performance data is being calculated
                    </p>
                    <p className="text-sm text-gray-500">
                      This includes collection efficiency, cash flow analysis, 
                      and performance scoring.
                    </p>
                  </CardBody>
                </Card>
              )}
            </Tab>
          </Tabs>
        </div>

        {/* Export Modal */}
        <Modal isOpen={isExportOpen} onClose={onExportClose}>
          <ModalContent>
            <ModalHeader>Export Analytics Data</ModalHeader>
            <ModalBody>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Export Format
                  </label>
                  <Select
                    selectedKeys={[exportFormat]}
                    onSelectionChange={(keys) => setExportFormat(Array.from(keys)[0] as string)}
                  >
                    <SelectItem key="json" value="json">JSON</SelectItem>
                    <SelectItem key="csv" value="csv">CSV</SelectItem>
                    <SelectItem key="pdf" value="pdf">PDF Report</SelectItem>
                  </Select>
                </div>

                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Export {activeView} analytics data for external analysis or reporting.
                </p>
              </div>
            </ModalBody>
            <ModalFooter>
              <Button variant="light" onPress={onExportClose}>
                Cancel
              </Button>
              <Button color="primary" onPress={handleExport}>
                Export Data
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>

        {/* Settings Modal */}
        <Modal isOpen={isSettingsOpen} onClose={onSettingsClose}>
          <ModalContent>
            <ModalHeader>Analytics Settings</ModalHeader>
            <ModalBody>
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Alerts & Notifications</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    Set up automated alerts for important metrics
                  </p>
                  
                  <Button
                    variant="flat"
                    onPress={handleCreateAlert}
                    className="w-full"
                  >
                    Create Revenue Alert
                  </Button>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Data Refresh</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Analytics data refreshes automatically every 5 minutes
                  </p>
                </div>
              </div>
            </ModalBody>
            <ModalFooter>
              <Button variant="light" onPress={onSettingsClose}>
                Close
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </Layout>
    </>
  );
};

export default AnalyticsPage;