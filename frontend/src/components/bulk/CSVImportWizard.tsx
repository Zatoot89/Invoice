import React, { useState } from 'react';
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Button,
  Card,
  CardBody,
  Progress,
  Tabs,
  Tab,
  Chip,
  Divider
} from '@nextui-org/react';
import { 
  DocumentArrowUpIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  DocumentArrowDownIcon 
} from '@heroicons/react/24/outline';
import CSVPreview from './CSVPreview';
import { toast } from 'react-hot-toast';

interface ImportResult {
  total_rows: number;
  successful_imports: number;
  updated_records: number;
  failed_imports: number;
  errors: Array<{ row: number; error: string }>;
}

interface CSVImportWizardProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  importType: 'customers' | 'invoices';
  onImportComplete: () => void;
}

const CUSTOMER_EXPECTED_COLUMNS = [
  'Name', 'Email', 'Phone', 'Company', 'Address Line 1', 'Address Line 2',
  'City', 'State', 'Postal Code', 'Country', 'Tax Number', 'Website',
  'Payment Terms', 'Preferred Currency', 'Is Active', 'Notes', 'Tags'
];

const CUSTOMER_REQUIRED_COLUMNS = ['Name', 'Email'];

export default function CSVImportWizard({
  isOpen,
  onOpenChange,
  importType,
  onImportComplete
}: CSVImportWizardProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isValidFile, setIsValidFile] = useState(false);
  const [validationErrors, setValidationErrors] = useState<any[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [importResults, setImportResults] = useState<ImportResult | null>(null);
  const [updateExisting, setUpdateExisting] = useState(false);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.csv')) {
        toast.error('Please select a CSV file');
        return;
      }
      
      if (file.size > 10 * 1024 * 1024) { // 10MB limit
        toast.error('File size too large (max 10MB)');
        return;
      }

      setSelectedFile(file);
      setCurrentStep(2);
    }
  };

  const handleValidationComplete = (isValid: boolean, errors: any[]) => {
    setIsValidFile(isValid);
    setValidationErrors(errors);
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

  const handleImport = async () => {
    if (!selectedFile || !isValidFile) {
      toast.error('Please select a valid file');
      return;
    }

    setIsUploading(true);
    setCurrentStep(3);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('update_existing', updateExisting.toString());

      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await fetch('/api/v1/bulk/import/customers', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      const result = await response.json();
      
      if (!response.ok) throw new Error(result.detail || 'Import failed');

      setImportResults(result.results);
      setCurrentStep(4);
      toast.success('Import completed successfully');
      onImportComplete();

    } catch (error) {
      toast.error(`Import failed: ${error.message}`);
      setCurrentStep(2); // Go back to validation step
    } finally {
      setIsUploading(false);
    }
  };

  const resetWizard = () => {
    setCurrentStep(1);
    setSelectedFile(null);
    setIsValidFile(false);
    setValidationErrors([]);
    setIsUploading(false);
    setUploadProgress(0);
    setImportResults(null);
    setUpdateExisting(false);
  };

  const handleClose = () => {
    resetWizard();
    onOpenChange(false);
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <DocumentArrowUpIcon className="mx-auto h-12 w-12 text-blue-500 mb-4" />
              <h3 className="text-lg font-semibold mb-2">Import {importType}</h3>
              <p className="text-gray-600 mb-6">
                Select a CSV file to import {importType}. Make sure your file follows the correct format.
              </p>
            </div>

            <Card>
              <CardBody>
                <h4 className="font-semibold mb-3">Before you start:</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• Download our template to see the correct format</li>
                  <li>• Required columns: {CUSTOMER_REQUIRED_COLUMNS.join(', ')}</li>
                  <li>• Maximum file size: 10MB</li>
                  <li>• File format: CSV only</li>
                </ul>
              </CardBody>
            </Card>

            <div className="flex gap-4">
              <Button
                variant="bordered"
                startContent={<DocumentArrowDownIcon className="h-4 w-4" />}
                onPress={downloadTemplate}
              >
                Download Template
              </Button>
              <Button
                color="primary"
                startContent={<DocumentArrowUpIcon className="h-4 w-4" />}
                onPress={() => document.getElementById('file-input')?.click()}
              >
                Select CSV File
              </Button>
            </div>

            <input
              id="file-input"
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>
        );

      case 2:
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Validate Data</h3>
              <Chip
                color={isValidFile ? 'success' : 'danger'}
                startContent={
                  isValidFile ? 
                    <CheckCircleIcon className="h-4 w-4" /> : 
                    <XCircleIcon className="h-4 w-4" />
                }
              >
                {isValidFile ? 'Valid' : 'Has Issues'}
              </Chip>
            </div>

            {selectedFile && (
              <CSVPreview
                file={selectedFile}
                onValidationComplete={handleValidationComplete}
                expectedColumns={CUSTOMER_EXPECTED_COLUMNS}
                requiredColumns={CUSTOMER_REQUIRED_COLUMNS}
              />
            )}

            <Card>
              <CardBody>
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="updateExisting"
                    checked={updateExisting}
                    onChange={(e) => setUpdateExisting(e.target.checked)}
                    className="rounded"
                  />
                  <label htmlFor="updateExisting" className="text-sm">
                    Update existing records with matching email addresses
                  </label>
                </div>
              </CardBody>
            </Card>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6 text-center">
            <div>
              <div className="mx-auto h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <DocumentArrowUpIcon className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Importing Data</h3>
              <p className="text-gray-600">Please wait while we process your file...</p>
            </div>

            <div className="space-y-2">
              <Progress
                value={uploadProgress}
                color="primary"
                className="max-w-md mx-auto"
              />
              <p className="text-sm text-gray-500">{uploadProgress}% complete</p>
            </div>

            {selectedFile && (
              <div className="text-sm text-gray-600">
                Processing: {selectedFile.name}
              </div>
            )}
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="mx-auto h-12 w-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <CheckCircleIcon className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Import Complete</h3>
              <p className="text-gray-600">Your data has been processed successfully.</p>
            </div>

            {importResults && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card>
                    <CardBody className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{importResults.total_rows}</div>
                      <div className="text-sm text-gray-600">Total Rows</div>
                    </CardBody>
                  </Card>
                  <Card>
                    <CardBody className="text-center">
                      <div className="text-2xl font-bold text-green-600">{importResults.successful_imports}</div>
                      <div className="text-sm text-gray-600">Imported</div>
                    </CardBody>
                  </Card>
                  <Card>
                    <CardBody className="text-center">
                      <div className="text-2xl font-bold text-orange-600">{importResults.updated_records}</div>
                      <div className="text-sm text-gray-600">Updated</div>
                    </CardBody>
                  </Card>
                  <Card>
                    <CardBody className="text-center">
                      <div className="text-2xl font-bold text-red-600">{importResults.failed_imports}</div>
                      <div className="text-sm text-gray-600">Failed</div>
                    </CardBody>
                  </Card>
                </div>

                {importResults.errors && importResults.errors.length > 0 && (
                  <Card>
                    <CardBody>
                      <h4 className="font-semibold text-red-600 mb-3">Import Errors:</h4>
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {importResults.errors.slice(0, 10).map((error, index) => (
                          <div key={index} className="text-sm bg-red-50 p-2 rounded">
                            <span className="font-medium">Row {error.row}: </span>
                            <span className="text-red-700">{error.error}</span>
                          </div>
                        ))}
                        {importResults.errors.length > 10 && (
                          <div className="text-sm text-gray-500 text-center">
                            ... and {importResults.errors.length - 10} more errors
                          </div>
                        )}
                      </div>
                    </CardBody>
                  </Card>
                )}
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  const getStepButtons = () => {
    switch (currentStep) {
      case 1:
        return (
          <Button variant="light" onPress={handleClose}>
            Cancel
          </Button>
        );

      case 2:
        return (
          <>
            <Button variant="light" onPress={() => setCurrentStep(1)}>
              Back
            </Button>
            <Button
              color="primary"
              onPress={handleImport}
              isDisabled={!isValidFile}
            >
              Import Data
            </Button>
          </>
        );

      case 3:
        return null; // No buttons during upload

      case 4:
        return (
          <>
            <Button variant="light" onPress={resetWizard}>
              Import Another File
            </Button>
            <Button color="primary" onPress={handleClose}>
              Done
            </Button>
          </>
        );

      default:
        return null;
    }
  };

  return (
    <Modal 
      isOpen={isOpen} 
      onOpenChange={onOpenChange}
      size="4xl"
      isDismissable={!isUploading}
      hideCloseButton={isUploading}
    >
      <ModalContent>
        {(onClose) => (
          <>
            <ModalHeader>
              <div className="flex items-center gap-4">
                <h2 className="text-xl font-semibold">CSV Import Wizard</h2>
                <div className="flex gap-2">
                  {[1, 2, 3, 4].map((step) => (
                    <div
                      key={step}
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                        step === currentStep
                          ? 'bg-blue-600 text-white'
                          : step < currentStep
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-200 text-gray-600'
                      }`}
                    >
                      {step < currentStep ? <CheckCircleIcon className="h-5 w-5" /> : step}
                    </div>
                  ))}
                </div>
              </div>
            </ModalHeader>

            <Divider />

            <ModalBody className="py-6">
              {renderStepContent()}
            </ModalBody>

            {getStepButtons() && (
              <>
                <Divider />
                <ModalFooter>
                  {getStepButtons()}
                </ModalFooter>
              </>
            )}
          </>
        )}
      </ModalContent>
    </Modal>
  );
}