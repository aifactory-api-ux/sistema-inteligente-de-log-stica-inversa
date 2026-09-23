import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle, CheckCircle, X } from 'lucide-react';
import { tokens } from '../../styles/tokens';
import { apiUploadFile } from '../../lib/api';
import type { BatchUploadResponse, BatchUploadRecord } from '../../types/models';

interface BatchUploadZoneProps {
  customerId: string;
  returnReason: string;
  onUploadComplete?: (response: BatchUploadResponse) => void;
  onError?: (error: string) => void;
  kamApprovalReference?: string;
}

interface ParsedRow {
  sku: string;
  quantity: number;
  reason_code: string;
  batch_id?: string;
  weight_kg?: number;
  volume_m3?: number;
}

export const BatchUploadZone: React.FC<BatchUploadZoneProps> = ({
  customerId,
  returnReason,
  onUploadComplete,
  onError,
  kamApprovalReference,
}) => {
  const [uploadState, setUploadState] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [uploadResult, setUploadResult] = useState<BatchUploadResponse | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const validateCSV = (content: string): { valid: boolean; errors: string[]; rows: ParsedRow[] } => {
    const lines = content.trim().split('\n');
    const errors: string[] = [];
    const rows: ParsedRow[] = [];

    if (lines.length < 2) {
      errors.push('CSV must have a header row and at least one data row');
      return { valid: false, errors, rows };
    }

    const header = lines[0].toLowerCase().split(',').map((h) => h.trim());
    const requiredHeaders = ['sku', 'quantity', 'reason_code'];
    const missingHeaders = requiredHeaders.filter((h) => !header.includes(h));
    if (missingHeaders.length > 0) {
      errors.push(`Missing required headers: ${missingHeaders.join(', ')}`);
    }

    const skuIndex = header.indexOf('sku');
    const quantityIndex = header.indexOf('quantity');
    const reasonIndex = header.indexOf('reason_code');
    const batchIndex = header.indexOf('batch_id');
    const weightIndex = header.indexOf('weight_kg');
    const volumeIndex = header.indexOf('volume_m3');

    for (let i = 1; i < lines.length; i++) {
      const columns = lines[i].split(',').map((c) => c.trim());

      if (columns.length < 3) {
        errors.push(`Row ${i + 1}: Insufficient columns`);
        continue;
      }

      const sku = columns[skuIndex] || columns[0];
      const quantity = parseInt(columns[quantityIndex] || columns[1], 10);
      const reason_code = columns[reasonIndex] || columns[2];

      if (!sku) errors.push(`Row ${i + 1}: Missing SKU`);
      if (isNaN(quantity) || quantity < 1) errors.push(`Row ${i + 1}: Invalid quantity`);
      if (!reason_code) errors.push(`Row ${i + 1}: Missing reason code`);

      rows.push({
        sku,
        quantity: isNaN(quantity) ? 0 : quantity,
        reason_code,
        batch_id: batchIndex >= 0 ? columns[batchIndex] : undefined,
        weight_kg: weightIndex >= 0 ? parseFloat(columns[weightIndex]) : undefined,
        volume_m3: volumeIndex >= 0 ? parseFloat(columns[volumeIndex]) : undefined,
      });
    }

    return { valid: errors.length === 0, errors, rows };
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setSelectedFile(file);

    const reader = new FileReader();
    reader.onload = async (e) => {
      const content = e.target?.result as string;
      const validation = validateCSV(content);

      if (!validation.valid) {
        setValidationErrors(validation.errors);
        setUploadState('error');
        onError?.(validation.errors.join('; '));
        return;
      }

      setValidationErrors([]);
      setUploadState('uploading');

      try {
        const additionalFields: Record<string, string> = {
          customer_id: customerId,
          return_reason: returnReason,
        };
        if (kamApprovalReference) {
          additionalFields.kam_approval_reference = kamApprovalReference;
        }

        const response = await apiUploadFile<BatchUploadResponse>(
          '/api/v1/batches/upload',
          file,
          additionalFields
        );

        setUploadResult(response);
        setUploadState('success');
        onUploadComplete?.(response);
      } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : 'Upload failed';
        setValidationErrors([errorMessage]);
        setUploadState('error');
        onError?.(errorMessage);
      }
    };
    reader.readAsText(file);
  }, [customerId, returnReason, kamApprovalReference, onUploadComplete, onError]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls', '.xlsx'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
    disabled: uploadState === 'uploading',
  });

  const resetUpload = () => {
    setUploadState('idle');
    setUploadResult(null);
    setValidationErrors([]);
    setSelectedFile(null);
  };

  const renderIdleState = () => (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
        transition-all duration-200 ease-in-out
        ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'}
      `}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-3">
        <div className={`p-3 rounded-full ${isDragActive ? 'bg-blue-100' : 'bg-gray-100'}`}>
          <Upload className={`w-6 h-6 ${isDragActive ? 'text-blue-500' : 'text-gray-400'}`} />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-700">
            {isDragActive ? 'Suelta el archivo aquí' : 'Arrastra un archivo CSV o haz clic para seleccionar'}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Formatos: .csv, .xls, .xlsx (máx. 10MB)
          </p>
        </div>
      </div>
    </div>
  );

  const renderUploadingState = () => (
    <div className="border-2 border-dashed border-blue-300 rounded-xl p-8 text-center bg-blue-50">
      <div className="flex flex-col items-center gap-3">
        <div className="animate-spin p-3 rounded-full bg-blue-100">
          <Upload className="w-6 h-6 text-blue-500" />
        </div>
        <div>
          <p className="text-sm font-medium text-blue-700">Procesando archivo...</p>
          <p className="text-xs text-blue-500 mt-1">{selectedFile?.name}</p>
        </div>
      </div>
    </div>
  );

  const renderSuccessState = () => (
    <div className="border-2 border-green-300 rounded-xl p-6 bg-green-50">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-green-700">Carga completada</p>
            <p className="text-xs text-green-600 mt-1">
              {uploadResult?.total_records || 0} registros procesados
            </p>
          </div>
        </div>
        <button onClick={resetUpload} className="text-gray-400 hover:text-gray-600">
          <X className="w-4 h-4" />
        </button>
      </div>

      {uploadResult && (
        <div className="mt-4 grid grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-3 border border-green-200">
            <p className="text-xs text-gray-500">Registros válidos</p>
            <p className="text-lg font-semibold text-green-600">{uploadResult.valid_records}</p>
          </div>
          <div className="bg-white rounded-lg p-3 border border-red-200">
            <p className="text-xs text-gray-500">Registros inválidos</p>
            <p className="text-lg font-semibold text-red-600">{uploadResult.invalid_records}</p>
          </div>
          <div className="bg-white rounded-lg p-3 border border-gray-200">
            <p className="text-xs text-gray-500">Valor total</p>
            <p className="text-lg font-semibold text-gray-700">€{Number(uploadResult.total_value).toFixed(2)}</p>
          </div>
        </div>
      )}

      {uploadResult?.warnings && uploadResult.warnings.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-medium text-amber-600 mb-2">Advertencias:</p>
          <ul className="text-xs text-amber-700 space-y-1">
            {uploadResult.warnings.map((warning, idx) => (
              <li key={idx}>• {warning}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );

  const renderErrorState = () => (
    <div className="border-2 border-red-300 rounded-xl p-6 bg-red-50">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-700">Error en la carga</p>
            <p className="text-xs text-red-500 mt-1">{selectedFile?.name}</p>
          </div>
        </div>
        <button onClick={resetUpload} className="text-gray-400 hover:text-gray-600">
          <X className="w-4 h-4" />
        </button>
      </div>

      <ul className="text-xs text-red-700 space-y-1">
        {validationErrors.map((error, idx) => (
          <li key={idx}>• {error}</li>
        ))}
      </ul>

      <button
        onClick={resetUpload}
        className="mt-4 text-sm text-blue-600 hover:text-blue-700 font-medium"
      >
        Intentar de nuevo
      </button>
    </div>
  );

  return (
    <div className="space-y-4">
      {uploadState === 'idle' && renderIdleState()}
      {uploadState === 'uploading' && renderUploadingState()}
      {uploadState === 'success' && renderSuccessState()}
      {uploadState === 'error' && renderErrorState()}
    </div>
  );
};

export default BatchUploadZone;
