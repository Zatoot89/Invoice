import React from 'react';
import { NextUIProvider } from '@nextui-org/react';
import { Toaster } from 'react-hot-toast';
import DashboardLayout from '../components/layout/DashboardLayout';
import BulkOperationsDashboard from '../components/bulk/BulkOperationsDashboard';

export default function BulkOperationsPage() {
  return (
    <NextUIProvider>
      <DashboardLayout>
        <div className="container mx-auto px-4 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Bulk Operations</h1>
            <p className="text-gray-600">
              Import, export, and manage your invoices and customers in bulk.
            </p>
          </div>
          
          <BulkOperationsDashboard />
        </div>
        
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#4ade80',
                secondary: '#fff',
              },
            },
            error: {
              duration: 5000,
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </DashboardLayout>
    </NextUIProvider>
  );
}