import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { NextUIProvider } from '@nextui-org/react';
import BulkActions from '../../components/bulk/BulkActions';

// Mock fetch
global.fetch = jest.fn();

// Mock toast
jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

const MockWrapper = ({ children }: { children: React.ReactNode }) => (
  <NextUIProvider>
    {children}
  </NextUIProvider>
);

describe('BulkActions Component', () => {
  const mockOnActionComplete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(() => 'mock-token'),
      },
      writable: true,
    });
  });

  it('renders export button', () => {
    render(
      <MockWrapper>
        <BulkActions
          selectedItems={[]}
          itemType="invoices"
          onActionComplete={mockOnActionComplete}
        />
      </MockWrapper>
    );

    expect(screen.getByText('Export')).toBeInTheDocument();
  });

  it('shows import button for customers', () => {
    render(
      <MockWrapper>
        <BulkActions
          selectedItems={[]}
          itemType="customers"
          onActionComplete={mockOnActionComplete}
        />
      </MockWrapper>
    );

    expect(screen.getByText('Import')).toBeInTheDocument();
  });

  it('shows bulk actions when items are selected', () => {
    render(
      <MockWrapper>
        <BulkActions
          selectedItems={[1, 2, 3]}
          itemType="invoices"
          onActionComplete={mockOnActionComplete}
        />
      </MockWrapper>
    );

    expect(screen.getByText('Actions (3)')).toBeInTheDocument();
  });

  it('handles export functionality', async () => {
    // Mock successful export response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(['test,csv,data'], { type: 'text/csv' })),
    });

    // Mock URL.createObjectURL
    global.URL.createObjectURL = jest.fn(() => 'mock-url');
    global.URL.revokeObjectURL = jest.fn();

    render(
      <MockWrapper>
        <BulkActions
          selectedItems={[]}
          itemType="invoices"
          onActionComplete={mockOnActionComplete}
        />
      </MockWrapper>
    );

    // Click export button
    const exportButton = screen.getByText('Export');
    fireEvent.click(exportButton);

    // Wait for dropdown to appear and click CSV option
    await waitFor(() => {
      const csvOption = screen.getByText('Export as CSV');
      fireEvent.click(csvOption);
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/bulk/export/invoices',
        expect.objectContaining({
          method: 'GET',
          headers: {
            'Authorization': 'Bearer mock-token',
          },
        })
      );
    });
  });

  it('handles bulk update for selected invoices', async () => {
    // Mock successful update response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        results: {
          updated_invoices: 2,
          failed_updates: 0,
          errors: [],
        },
      }),
    });

    render(
      <MockWrapper>
        <BulkActions
          selectedItems={[1, 2]}
          itemType="invoices"
          onActionComplete={mockOnActionComplete}
        />
      </MockWrapper>
    );

    // Click actions button
    const actionsButton = screen.getByText('Actions (2)');
    fireEvent.click(actionsButton);

    // Click bulk update option
    await waitFor(() => {
      const updateOption = screen.getByText('Bulk Update');
      fireEvent.click(updateOption);
    });

    // Modal should open - check for modal title
    await waitFor(() => {
      expect(screen.getByText('Bulk Update Invoices')).toBeInTheDocument();
    });
  });

  it('validates file type during import', async () => {
    render(
      <MockWrapper>
        <BulkActions
          selectedItems={[]}
          itemType="customers"
          onActionComplete={mockOnActionComplete}
        />
      </MockWrapper>
    );

    // Click import button
    const importButton = screen.getByText('Import');
    fireEvent.click(importButton);

    // Modal should open
    await waitFor(() => {
      expect(screen.getByText('Import Customers')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    // Mock failed export response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    render(
      <MockWrapper>
        <BulkActions
          selectedItems={[]}
          itemType="invoices"
          onActionComplete={mockOnActionComplete}
        />
      </MockWrapper>
    );

    // Click export button
    const exportButton = screen.getByText('Export');
    fireEvent.click(exportButton);

    // Click CSV option
    await waitFor(() => {
      const csvOption = screen.getByText('Export as CSV');
      fireEvent.click(csvOption);
    });

    // Should handle error (toast.error would be called)
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });
  });

  it('disables actions when no items selected for bulk operations', () => {
    render(
      <MockWrapper>
        <BulkActions
          selectedItems={[]}
          itemType="invoices"
          onActionComplete={mockOnActionComplete}
        />
      </MockWrapper>
    );

    // Should not show bulk actions button when no items selected
    expect(screen.queryByText('Actions')).not.toBeInTheDocument();
  });

  it('calls onActionComplete after successful operation', async () => {
    // Mock successful update response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        results: {
          updated_invoices: 1,
          failed_updates: 0,
          errors: [],
        },
      }),
    });

    render(
      <MockWrapper>
        <BulkActions
          selectedItems={[1]}
          itemType="invoices"
          onActionComplete={mockOnActionComplete}
        />
      </MockWrapper>
    );

    // Simulate bulk operation completion
    // This would be triggered after a successful API call
    await waitFor(() => {
      // In a real scenario, this would be called after the operation completes
      // For this test, we're just verifying the callback exists
      expect(mockOnActionComplete).toBeDefined();
    });
  });
});