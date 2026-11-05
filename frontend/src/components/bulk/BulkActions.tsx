import React, { useState, useRef } from 'react';
import {
  Button,
  Dropdown,
  DropdownTrigger,
  DropdownMenu,
  DropdownItem,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Input,
  Select,
  SelectItem,
  Textarea,
  useDisclosure,
  Chip,
  Progress,
  Card,
  CardBody
} from '@nextui-org/react';
import { 
  ChevronDownIcon, 
  DocumentArrowDownIcon, 
  DocumentArrowUpIcon,
  TrashIcon,
  PaperAirplaneIcon,
  PencilSquareIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

interface BulkActionsProps {
  selectedItems: number[];
  itemType: 'invoices' | 'customers';
  onActionComplete: () => void;
}

interface BulkOperationResult {
  total_invoices?: number;
  updated_invoices?: number;
  failed_updates?: number;
  sent_invoices?: number;
  failed_sends?: number;
  deleted_invoices?: number;
  skipped_invoices?: number;
  successful_imports?: number;
  failed_imports?: number;
  errors?: Array<{ invoice_id?: number; row?: number; error: string }>;
}

export default function BulkActions({ selectedItems, itemType, onActionComplete }: BulkActionsProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [operationResults, setOperationResults] = useState<BulkOperationResult | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Modals
  const updateModal = useDisclosure();
  const deleteModal = useDisclosure();
  const resultsModal = useDisclosure();
  const importModal = useDisclosure();
  
  // Form states
  const [updateData, setUpdateData] = useState({
    status: '',
    due_date: '',
    notes: '',
    terms_and_conditions: ''
  });
  
  const [deleteForce, setDeleteForce] = useState(false);
  const [updateExisting, setUpdateExisting] = useState(false);

  const handleExport = async (format: 'csv') => {
    setIsLoading(true);
    try {
      const endpoint = itemType === 'invoices' ? '/api/v1/bulk/export/invoices' : '/api/v1/bulk/export/customers';
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${itemType}_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success(`${itemType} exported successfully`);
    } catch (error) {
      toast.error(`Export failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleImport = async (file: File) => {
    setIsLoading(true);
    setUploadProgress(0);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('update_existing', updateExisting.toString());

      const response = await fetch('/api/v1/bulk/import/customers', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      const result = await response.json();
      
      if (!response.ok) throw new Error(result.detail || 'Import failed');

      setOperationResults(result.results);
      resultsModal.onOpen();
      toast.success('Import completed');
      onActionComplete();
    } catch (error) {
      toast.error(`Import failed: ${error.message}`);
    } finally {
      setIsLoading(false);
      setUploadProgress(0);
      importModal.onClose();
    }
  };

  const handleBulkUpdate = async () => {
    if (selectedItems.length === 0) {
      toast.error('Please select items to update');
      return;
    }

    setIsLoading(true);
    try {
      const updates: any = {};
      if (updateData.status) updates.status = updateData.status;
      if (updateData.due_date) updates.due_date = updateData.due_date;
      if (updateData.notes) updates.notes = updateData.notes;
      if (updateData.terms_and_conditions) updates.terms_and_conditions = updateData.terms_and_conditions;

      const response = await fetch('/api/v1/bulk/invoices/update', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          invoice_ids: selectedItems,
          updates
        })
      });

      const result = await response.json();
      
      if (!response.ok) throw new Error(result.detail || 'Update failed');

      setOperationResults(result.results);
      resultsModal.onOpen();
      toast.success('Bulk update completed');
      onActionComplete();
    } catch (error) {
      toast.error(`Update failed: ${error.message}`);
    } finally {
      setIsLoading(false);
      updateModal.onClose();
    }
  };

  const handleBulkSend = async () => {
    if (selectedItems.length === 0) {
      toast.error('Please select invoices to send');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/bulk/invoices/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          invoice_ids: selectedItems
        })
      });

      const result = await response.json();
      
      if (!response.ok) throw new Error(result.detail || 'Send failed');

      setOperationResults(result.results);
      resultsModal.onOpen();
      toast.success('Bulk send completed');
      onActionComplete();
    } catch (error) {
      toast.error(`Send failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedItems.length === 0) {
      toast.error('Please select items to delete');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/bulk/invoices/delete', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          invoice_ids: selectedItems,
          force: deleteForce
        })
      });

      const result = await response.json();
      
      if (!response.ok) throw new Error(result.detail || 'Delete failed');

      setOperationResults(result.results);
      resultsModal.onOpen();
      toast.success('Bulk delete completed');
      onActionComplete();
    } catch (error) {
      toast.error(`Delete failed: ${error.message}`);
    } finally {
      setIsLoading(false);
      deleteModal.onClose();
    }
  };

  const downloadTemplate = async () => {
    try {
      const response = await fetch('/api/v1/bulk/template/customers', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Template download failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'customer_import_template.csv';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success('Template downloaded successfully');
    } catch (error) {
      toast.error(`Template download failed: ${error.message}`);
    }
  };

  return (
    <div className="flex gap-2 items-center">
      {/* Export Dropdown */}
      <Dropdown>
        <DropdownTrigger>
          <Button
            variant="bordered"
            startContent={<DocumentArrowDownIcon className="h-4 w-4" />}
            endContent={<ChevronDownIcon className="h-4 w-4" />}
            isLoading={isLoading}
          >
            Export
          </Button>
        </DropdownTrigger>
        <DropdownMenu>
          <DropdownItem
            key="csv"
            startContent={<DocumentArrowDownIcon className="h-4 w-4" />}
            onPress={() => handleExport('csv')}
          >
            Export as CSV
          </DropdownItem>
        </DropdownMenu>
      </Dropdown>

      {/* Import Button (only for customers) */}
      {itemType === 'customers' && (
        <Button
          variant="bordered"
          startContent={<DocumentArrowUpIcon className="h-4 w-4" />}
          onPress={importModal.onOpen}
        >
          Import
        </Button>
      )}

      {/* Bulk Actions (only if items are selected) */}
      {selectedItems.length > 0 && (
        <Dropdown>
          <DropdownTrigger>
            <Button
              color="primary"
              startContent={<PencilSquareIcon className="h-4 w-4" />}
              endContent={<ChevronDownIcon className="h-4 w-4" />}
            >
              Actions ({selectedItems.length})
            </Button>
          </DropdownTrigger>
          <DropdownMenu>
            {itemType === 'invoices' && (
              <>
                <DropdownItem
                  key="update"
                  startContent={<PencilSquareIcon className="h-4 w-4" />}
                  onPress={updateModal.onOpen}
                >
                  Bulk Update
                </DropdownItem>
                <DropdownItem
                  key="send"
                  startContent={<PaperAirplaneIcon className="h-4 w-4" />}
                  onPress={handleBulkSend}
                >
                  Send Invoices
                </DropdownItem>
              </>
            )}
            <DropdownItem
              key="delete"
              className="text-danger"
              color="danger"
              startContent={<TrashIcon className="h-4 w-4" />}
              onPress={deleteModal.onOpen}
            >
              Delete Selected
            </DropdownItem>
          </DropdownMenu>
        </Dropdown>
      )}

      {/* Import Modal */}
      <Modal isOpen={importModal.isOpen} onOpenChange={importModal.onOpenChange} size="2xl">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader>Import Customers</ModalHeader>
              <ModalBody>
                <div className="space-y-4">
                  <div className="text-sm text-gray-600">
                    Upload a CSV file to import customers. You can download a template to see the required format.
                  </div>
                  
                  <Button
                    variant="bordered"
                    onPress={downloadTemplate}
                    startContent={<DocumentArrowDownIcon className="h-4 w-4" />}
                  >
                    Download Template
                  </Button>

                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".csv"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleImport(file);
                      }}
                      className="hidden"
                    />
                    <Button
                      variant="ghost"
                      onPress={() => fileInputRef.current?.click()}
                      startContent={<DocumentArrowUpIcon className="h-8 w-8" />}
                      size="lg"
                    >
                      Choose CSV File
                    </Button>
                  </div>

                  {uploadProgress > 0 && (
                    <Progress value={uploadProgress} label="Uploading..." />
                  )}

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="updateExisting"
                      checked={updateExisting}
                      onChange={(e) => setUpdateExisting(e.target.checked)}
                    />
                    <label htmlFor="updateExisting" className="text-sm">
                      Update existing customers with matching email
                    </label>
                  </div>
                </div>
              </ModalBody>
              <ModalFooter>
                <Button variant="light" onPress={onClose}>
                  Cancel
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>

      {/* Update Modal */}
      <Modal isOpen={updateModal.isOpen} onOpenChange={updateModal.onOpenChange}>
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader>Bulk Update Invoices</ModalHeader>
              <ModalBody>
                <div className="space-y-4">
                  <Select
                    label="Status"
                    placeholder="Select new status"
                    value={updateData.status}
                    onChange={(e) => setUpdateData({...updateData, status: e.target.value})}
                  >
                    <SelectItem key="draft" value="draft">Draft</SelectItem>
                    <SelectItem key="sent" value="sent">Sent</SelectItem>
                    <SelectItem key="paid" value="paid">Paid</SelectItem>
                    <SelectItem key="cancelled" value="cancelled">Cancelled</SelectItem>
                  </Select>

                  <Input
                    type="date"
                    label="Due Date"
                    value={updateData.due_date}
                    onChange={(e) => setUpdateData({...updateData, due_date: e.target.value})}
                  />

                  <Textarea
                    label="Notes"
                    placeholder="Update invoice notes"
                    value={updateData.notes}
                    onChange={(e) => setUpdateData({...updateData, notes: e.target.value})}
                  />

                  <Textarea
                    label="Terms & Conditions"
                    placeholder="Update terms and conditions"
                    value={updateData.terms_and_conditions}
                    onChange={(e) => setUpdateData({...updateData, terms_and_conditions: e.target.value})}
                  />
                </div>
              </ModalBody>
              <ModalFooter>
                <Button variant="light" onPress={onClose}>
                  Cancel
                </Button>
                <Button
                  color="primary"
                  onPress={handleBulkUpdate}
                  isLoading={isLoading}
                >
                  Update {selectedItems.length} Invoice{selectedItems.length !== 1 ? 's' : ''}
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>

      {/* Delete Modal */}
      <Modal isOpen={deleteModal.isOpen} onOpenChange={deleteModal.onOpenChange}>
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader>Delete Selected Items</ModalHeader>
              <ModalBody>
                <div className="space-y-4">
                  <div className="text-sm text-gray-600">
                    Are you sure you want to delete {selectedItems.length} selected item{selectedItems.length !== 1 ? 's' : ''}?
                  </div>
                  
                  {itemType === 'invoices' && (
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="forceDelete"
                        checked={deleteForce}
                        onChange={(e) => setDeleteForce(e.target.checked)}
                      />
                      <label htmlFor="forceDelete" className="text-sm">
                        Force delete (allow deletion of non-draft invoices)
                      </label>
                    </div>
                  )}
                </div>
              </ModalBody>
              <ModalFooter>
                <Button variant="light" onPress={onClose}>
                  Cancel
                </Button>
                <Button
                  color="danger"
                  onPress={handleBulkDelete}
                  isLoading={isLoading}
                >
                  Delete
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>

      {/* Results Modal */}
      <Modal isOpen={resultsModal.isOpen} onOpenChange={resultsModal.onOpenChange} size="2xl">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader>Operation Results</ModalHeader>
              <ModalBody>
                {operationResults && (
                  <div className="space-y-4">
                    {/* Success Stats */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {operationResults.successful_imports !== undefined && (
                        <Card>
                          <CardBody className="text-center">
                            <div className="text-2xl font-bold text-green-600">{operationResults.successful_imports}</div>
                            <div className="text-sm text-gray-600">Imported</div>
                          </CardBody>
                        </Card>
                      )}
                      {operationResults.updated_invoices !== undefined && (
                        <Card>
                          <CardBody className="text-center">
                            <div className="text-2xl font-bold text-blue-600">{operationResults.updated_invoices}</div>
                            <div className="text-sm text-gray-600">Updated</div>
                          </CardBody>
                        </Card>
                      )}
                      {operationResults.sent_invoices !== undefined && (
                        <Card>
                          <CardBody className="text-center">
                            <div className="text-2xl font-bold text-purple-600">{operationResults.sent_invoices}</div>
                            <div className="text-sm text-gray-600">Sent</div>
                          </CardBody>
                        </Card>
                      )}
                      {operationResults.deleted_invoices !== undefined && (
                        <Card>
                          <CardBody className="text-center">
                            <div className="text-2xl font-bold text-red-600">{operationResults.deleted_invoices}</div>
                            <div className="text-sm text-gray-600">Deleted</div>
                          </CardBody>
                        </Card>
                      )}
                    </div>

                    {/* Errors */}
                    {operationResults.errors && operationResults.errors.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-red-600 mb-2">Errors:</h4>
                        <div className="space-y-2 max-h-60 overflow-y-auto">
                          {operationResults.errors.map((error, index) => (
                            <div key={index} className="bg-red-50 p-2 rounded text-sm">
                              {error.row && <span className="font-medium">Row {error.row}: </span>}
                              {error.invoice_id && <span className="font-medium">Invoice {error.invoice_id}: </span>}
                              <span className="text-red-700">{error.error}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </ModalBody>
              <ModalFooter>
                <Button onPress={onClose}>
                  Close
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </div>
  );
}