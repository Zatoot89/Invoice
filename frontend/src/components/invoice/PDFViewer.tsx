import { useState, useEffect } from 'react';
import { 
  Button, 
  Modal, 
  ModalContent, 
  ModalHeader, 
  ModalBody, 
  ModalFooter,
  Select,
  SelectItem,
  Spinner,
  Card,
  CardBody
} from '@nextui-org/react';
import { 
  DocumentArrowDownIcon,
  EyeIcon,
  PrinterIcon,
  ShareIcon 
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface PDFViewerProps {
  invoiceId: number;
  isOpen: boolean;
  onClose: () => void;
}

interface PDFTemplate {
  id: string;
  name: string;
  description: string;
}

const PDF_TEMPLATES: PDFTemplate[] = [
  {
    id: 'professional',
    name: 'Professional',
    description: 'Clean, modern design suitable for business use'
  },
  {
    id: 'modern', 
    name: 'Modern',
    description: 'Contemporary design with bold colors'
  },
  {
    id: 'classic',
    name: 'Classic', 
    description: 'Traditional invoice layout with serif fonts'
  }
];

export default function PDFViewer({ invoiceId, isOpen, onClose }: PDFViewerProps) {
  const [selectedTemplate, setSelectedTemplate] = useState('professional');
  const [isGenerating, setIsGenerating] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfData, setPdfData] = useState<{
    pdf_base64: string;
    filename: string;
    size_bytes: number;
  } | null>(null);

  useEffect(() => {
    if (isOpen && invoiceId) {
      generatePDF();
    }
    
    return () => {
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [isOpen, invoiceId, selectedTemplate]);

  const generatePDF = async () => {
    setIsGenerating(true);
    
    try {
      // In a real app, this would call your API
      const response = await fetch(`/api/v1/pdf/invoice/${invoiceId}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          template: selectedTemplate,
          download: false
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate PDF');
      }

      const data = await response.json();
      setPdfData(data);
      
      // Convert base64 to blob and create URL
      const pdfBlob = new Blob([
        Uint8Array.from(atob(data.pdf_base64), c => c.charCodeAt(0))
      ], { type: 'application/pdf' });
      
      const url = URL.createObjectURL(pdfBlob);
      setPdfUrl(url);
      
    } catch (error) {
      console.error('PDF generation error:', error);
      toast.error('Failed to generate PDF');
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadPDF = () => {
    if (!pdfData || !pdfUrl) return;
    
    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = pdfData.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    toast.success('PDF downloaded successfully');
  };

  const printPDF = () => {
    if (!pdfUrl) return;
    
    const printWindow = window.open(pdfUrl);
    if (printWindow) {
      printWindow.onload = () => {
        printWindow.print();
      };
    }
  };

  const sharePDF = async () => {
    if (!pdfData || !pdfUrl) return;
    
    if (navigator.share) {
      try {
        const response = await fetch(pdfUrl);
        const blob = await response.blob();
        const file = new File([blob], pdfData.filename, { type: 'application/pdf' });
        
        await navigator.share({
          title: `Invoice ${pdfData.filename}`,
          files: [file]
        });
      } catch (error) {
        console.error('Sharing failed:', error);
        toast.error('Sharing not supported');
      }
    } else {
      // Fallback: copy link to clipboard
      navigator.clipboard.writeText(pdfUrl);
      toast.success('PDF link copied to clipboard');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose}
      size="5xl"
      classNames={{
        base: "max-h-[95vh]",
        body: "p-0",
        header: "border-b border-gray-200 dark:border-gray-700"
      }}
    >
      <ModalContent>
        <ModalHeader className="flex flex-col gap-1">
          <div className="flex items-center justify-between w-full">
            <h3 className="text-lg font-semibold">Invoice PDF</h3>
            
            <div className="flex items-center gap-3">
              <Select
                label="Template"
                size="sm"
                value={selectedTemplate}
                onChange={(e) => setSelectedTemplate(e.target.value)}
                className="w-48"
                disabled={isGenerating}
              >
                {PDF_TEMPLATES.map((template) => (
                  <SelectItem key={template.id} value={template.id}>
                    {template.name}
                  </SelectItem>
                ))}
              </Select>
              
              {pdfData && (
                <span className="text-sm text-gray-500">
                  {formatFileSize(pdfData.size_bytes)}
                </span>
              )}
            </div>
          </div>
        </ModalHeader>

        <ModalBody className="p-0">
          {isGenerating ? (
            <div className="flex items-center justify-center h-96">
              <div className="text-center">
                <Spinner size="lg" />
                <p className="mt-4 text-gray-600 dark:text-gray-400">
                  Generating PDF...
                </p>
              </div>
            </div>
          ) : pdfUrl ? (
            <div className="h-[70vh] w-full">
              <iframe
                src={`${pdfUrl}#toolbar=1&navpanes=0`}
                className="w-full h-full border-0"
                title="PDF Preview"
              />
            </div>
          ) : (
            <div className="flex items-center justify-center h-96">
              <Card className="max-w-md">
                <CardBody className="text-center">
                  <DocumentArrowDownIcon className="mx-auto h-16 w-16 text-gray-400 mb-4" />
                  <p className="text-gray-600 dark:text-gray-400">
                    No PDF generated yet
                  </p>
                </CardBody>
              </Card>
            </div>
          )}
        </ModalBody>

        <ModalFooter className="border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between w-full">
            <div className="text-sm text-gray-500">
              {pdfData?.filename}
            </div>
            
            <div className="flex gap-2">
              <Button
                variant="light"
                startContent={<EyeIcon className="h-4 w-4" />}
                onClick={() => generatePDF()}
                disabled={isGenerating}
              >
                Refresh
              </Button>
              
              <Button
                variant="light"
                startContent={<PrinterIcon className="h-4 w-4" />}
                onClick={printPDF}
                disabled={!pdfUrl || isGenerating}
              >
                Print
              </Button>
              
              <Button
                variant="light"
                startContent={<ShareIcon className="h-4 w-4" />}
                onClick={sharePDF}
                disabled={!pdfUrl || isGenerating}
              >
                Share
              </Button>
              
              <Button
                color="primary"
                startContent={<DocumentArrowDownIcon className="h-4 w-4" />}
                onClick={downloadPDF}
                disabled={!pdfUrl || isGenerating}
              >
                Download
              </Button>
              
              <Button variant="light" onClick={onClose}>
                Close
              </Button>
            </div>
          </div>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}