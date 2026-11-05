import React, { useState, useEffect } from 'react';
import {
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  Card,
  CardHeader,
  CardBody,
  Chip,
  Button,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useDisclosure
} from '@nextui-org/react';
import { CheckCircleIcon, XCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface CSVRow {
  [key: string]: string;
}

interface ValidationError {
  row: number;
  column: string;
  error: string;
  severity: 'error' | 'warning';
}

interface CSVPreviewProps {
  file: File | null;
  onValidationComplete: (isValid: boolean, errors: ValidationError[]) => void;
  expectedColumns: string[];
  requiredColumns: string[];
}

export default function CSVPreview({ 
  file, 
  onValidationComplete, 
  expectedColumns, 
  requiredColumns 
}: CSVPreviewProps) {
  const [csvData, setCsvData] = useState<CSVRow[]>([]);
  const [headers, setHeaders] = useState<string[]>([]);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [previewRows, setPreviewRows] = useState(5);
  
  const errorModal = useDisclosure();

  useEffect(() => {
    if (file) {
      parseCSVFile(file);
    }
  }, [file]);

  const parseCSVFile = async (file: File) => {
    setIsLoading(true);
    try {
      const text = await file.text();
      const lines = text.split('\n').filter(line => line.trim());
      
      if (lines.length === 0) {
        onValidationComplete(false, [{ row: 0, column: 'file', error: 'File is empty', severity: 'error' }]);
        return;
      }

      // Parse headers
      const headerLine = lines[0];
      const parsedHeaders = parseCSVLine(headerLine);
      setHeaders(parsedHeaders);

      // Parse data rows
      const rows: CSVRow[] = [];
      for (let i = 1; i < lines.length; i++) {
        const values = parseCSVLine(lines[i]);
        const row: CSVRow = {};
        parsedHeaders.forEach((header, index) => {
          row[header] = values[index] || '';
        });
        rows.push(row);
      }

      setCsvData(rows);
      
      // Validate data
      const errors = validateCSVData(parsedHeaders, rows);
      setValidationErrors(errors);
      
      const hasErrors = errors.some(error => error.severity === 'error');
      onValidationComplete(!hasErrors, errors);
      
    } catch (error) {
      onValidationComplete(false, [{ 
        row: 0, 
        column: 'file', 
        error: `Failed to parse CSV: ${error.message}`, 
        severity: 'error' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const parseCSVLine = (line: string): string[] => {
    const result = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      
      if (char === '"') {
        if (inQuotes && line[i + 1] === '"') {
          current += '"';
          i++; // Skip next quote
        } else {
          inQuotes = !inQuotes;
        }
      } else if (char === ',' && !inQuotes) {
        result.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    
    result.push(current.trim());
    return result;
  };

  const validateCSVData = (headers: string[], rows: CSVRow[]): ValidationError[] => {
    const errors: ValidationError[] = [];

    // Check for required columns
    requiredColumns.forEach(reqCol => {
      const found = headers.find(header => 
        header.toLowerCase().trim() === reqCol.toLowerCase().trim()
      );
      if (!found) {
        errors.push({
          row: 0,
          column: reqCol,
          error: `Required column '${reqCol}' is missing`,
          severity: 'error'
        });
      }
    });

    // Check for unexpected columns
    headers.forEach(header => {
      const expected = expectedColumns.find(expCol =>
        expCol.toLowerCase().trim() === header.toLowerCase().trim()
      );
      if (!expected) {
        errors.push({
          row: 0,
          column: header,
          error: `Unexpected column '${header}'`,
          severity: 'warning'
        });
      }
    });

    // Validate row data
    rows.forEach((row, index) => {
      const rowNumber = index + 2; // +2 because row 1 is headers, and we want 1-based indexing

      // Check required fields
      requiredColumns.forEach(reqCol => {
        const header = headers.find(h => h.toLowerCase().trim() === reqCol.toLowerCase().trim());
        if (header && !row[header]?.trim()) {
          errors.push({
            row: rowNumber,
            column: reqCol,
            error: `Required field '${reqCol}' is empty`,
            severity: 'error'
          });
        }
      });

      // Validate email format
      const emailHeader = headers.find(h => h.toLowerCase().includes('email'));
      if (emailHeader && row[emailHeader]) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(row[emailHeader])) {
          errors.push({
            row: rowNumber,
            column: emailHeader,
            error: 'Invalid email format',
            severity: 'error'
          });
        }
      }

      // Validate numeric fields
      const numericFields = ['Payment Terms'];
      numericFields.forEach(field => {
        const header = headers.find(h => h.toLowerCase().trim() === field.toLowerCase().trim());
        if (header && row[header] && isNaN(Number(row[header]))) {
          errors.push({
            row: rowNumber,
            column: field,
            error: `'${field}' must be a number`,
            severity: 'error'
          });
        }
      });

      // Validate boolean fields
      const booleanFields = ['Is Active'];
      booleanFields.forEach(field => {
        const header = headers.find(h => h.toLowerCase().trim() === field.toLowerCase().trim());
        if (header && row[header]) {
          const value = row[header].toLowerCase();
          if (!['true', 'false', '1', '0', 'yes', 'no', ''].includes(value)) {
            errors.push({
              row: rowNumber,
              column: field,
              error: `'${field}' must be true/false, yes/no, or 1/0`,
              severity: 'warning'
            });
          }
        }
      });
    });

    return errors;
  };

  const getErrorsForRow = (rowIndex: number): ValidationError[] => {
    return validationErrors.filter(error => error.row === rowIndex + 2);
  };

  const getErrorsForColumn = (column: string): ValidationError[] => {
    return validationErrors.filter(error => error.column === column);
  };

  const errorCount = validationErrors.filter(e => e.severity === 'error').length;
  const warningCount = validationErrors.filter(e => e.severity === 'warning').length;

  if (!file) {
    return null;
  }

  if (isLoading) {
    return (
      <Card>
        <CardBody>
          <div className="flex items-center justify-center py-8">
            <div>Loading CSV preview...</div>
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Validation Summary */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <h3 className="text-lg font-semibold">CSV Validation Summary</h3>
            <div className="flex gap-2">
              {errorCount > 0 && (
                <Chip
                  color="danger"
                  variant="flat"
                  startContent={<XCircleIcon className="h-4 w-4" />}
                >
                  {errorCount} Error{errorCount !== 1 ? 's' : ''}
                </Chip>
              )}
              {warningCount > 0 && (
                <Chip
                  color="warning"
                  variant="flat"
                  startContent={<ExclamationTriangleIcon className="h-4 w-4" />}
                >
                  {warningCount} Warning{warningCount !== 1 ? 's' : ''}
                </Chip>
              )}
              {errorCount === 0 && warningCount === 0 && (
                <Chip
                  color="success"
                  variant="flat"
                  startContent={<CheckCircleIcon className="h-4 w-4" />}
                >
                  Valid
                </Chip>
              )}
            </div>
          </div>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">{csvData.length}</div>
              <div className="text-sm text-gray-600">Total Rows</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">{headers.length}</div>
              <div className="text-sm text-gray-600">Columns</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">
                {Math.round((file.size / 1024) * 100) / 100} KB
              </div>
              <div className="text-sm text-gray-600">File Size</div>
            </div>
          </div>
          
          {validationErrors.length > 0 && (
            <div className="mt-4">
              <Button
                size="sm"
                color="danger"
                variant="light"
                onPress={errorModal.onOpen}
              >
                View All Issues ({validationErrors.length})
              </Button>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Data Preview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <h3 className="text-lg font-semibold">Data Preview</h3>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="light"
                onPress={() => setPreviewRows(Math.min(previewRows + 5, csvData.length))}
                isDisabled={previewRows >= csvData.length}
              >
                Show More
              </Button>
              <Button
                size="sm"
                variant="light"
                onPress={() => setPreviewRows(Math.max(previewRows - 5, 5))}
                isDisabled={previewRows <= 5}
              >
                Show Less
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardBody>
          {csvData.length > 0 && (
            <div className="overflow-x-auto">
              <Table aria-label="CSV Data Preview">
                <TableHeader>
                  {headers.map((header, index) => (
                    <TableColumn key={index}>
                      <div className="flex items-center gap-1">
                        {header}
                        {getErrorsForColumn(header).length > 0 && (
                          <XCircleIcon className="h-4 w-4 text-red-500" />
                        )}
                      </div>
                    </TableColumn>
                  ))}
                </TableHeader>
                <TableBody>
                  {csvData.slice(0, previewRows).map((row, rowIndex) => {
                    const rowErrors = getErrorsForRow(rowIndex);
                    return (
                      <TableRow
                        key={rowIndex}
                        className={rowErrors.some(e => e.severity === 'error') ? 'bg-red-50' : ''}
                      >
                        {headers.map((header, colIndex) => (
                          <TableCell key={colIndex}>
                            <div className="flex items-center gap-1">
                              {row[header] || ''}
                              {rowErrors.some(e => e.column === header && e.severity === 'error') && (
                                <XCircleIcon className="h-4 w-4 text-red-500" />
                              )}
                              {rowErrors.some(e => e.column === header && e.severity === 'warning') && (
                                <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500" />
                              )}
                            </div>
                          </TableCell>
                        ))}
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Errors Modal */}
      <Modal isOpen={errorModal.isOpen} onOpenChange={errorModal.onOpenChange} size="2xl">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader>Validation Issues</ModalHeader>
              <ModalBody>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {validationErrors.map((error, index) => (
                    <div
                      key={index}
                      className={`p-3 rounded border-l-4 ${
                        error.severity === 'error'
                          ? 'bg-red-50 border-red-500'
                          : 'bg-yellow-50 border-yellow-500'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        {error.severity === 'error' ? (
                          <XCircleIcon className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                        ) : (
                          <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                        )}
                        <div>
                          <div className="font-medium">
                            {error.row === 0 ? 'Header' : `Row ${error.row}`}
                            {error.row !== 0 && `, Column: ${error.column}`}
                          </div>
                          <div className="text-sm text-gray-600">{error.error}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ModalBody>
              <ModalFooter>
                <Button onPress={onClose}>Close</Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </div>
  );
}