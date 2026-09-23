import React, { useState, useCallback } from 'react';
import { User, Building2, AlertCircle } from 'lucide-react';
import { tokens } from '../styles/tokens';
import { returnsApi, batchesApi } from '../services/api';
import { ProfileSelector } from '../components/ui/ProfileSelector';
import { ReturnForm } from '../components/ui/ReturnForm';
import { BatchUploadZone } from '../components/ui/BatchUploadZone';
import { DecisionOutcomeCard } from '../components/ui/DecisionOutcomeCard';
import { PrimaryButtonCTA } from '../components/ui/PrimaryButtonCTA';
import { StatusBadge } from '../components/ui/StatusBadge';
import type {
  ReturnChannel,
  ReturnItem,
  ReturnRequestCreate,
  DecisionResult,
  BatchUploadResponse,
  ReturnRequest,
} from '../types/models';

interface FormData {
  customer_id: string;
  customer_type: string;
  order_reference: string;
  invoice_reference: string;
  return_reason: string;
  return_reason_description: string;
  contact_email: string;
  contact_phone: string;
  items: ReturnItem[];
}

interface FormErrors {
  [key: string]: string;
}

export const ReturnPortalPage: React.FC = () => {
  const [selectedProfile, setSelectedProfile] = useState<'B2C' | 'B2B' | null>(null);
  const [formData, setFormData] = useState<FormData>({
    customer_id: '',
    customer_type: '',
    order_reference: '',
    invoice_reference: '',
    return_reason: '',
    return_reason_description: '',
    contact_email: '',
    contact_phone: '',
    items: [],
  });
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [currentItem, setCurrentItem] = useState<Partial<ReturnItem>>({
    sku: '',
    product_name: '',
    quantity: 1,
    unit_price: 0,
    weight_kg: 0,
    volume_m3: 0,
    reason_code: '',
    condition: 'NEW',
  });
  const [decisionResult, setDecisionResult] = useState<DecisionResult | null>(null);
  const [currentReturn, setCurrentReturn] = useState<ReturnRequest | null>(null);
  const [batchResult, setBatchResult] = useState<BatchUploadResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const validateForm = useCallback((): boolean => {
    const errors: FormErrors = {};

    if (!formData.customer_id.trim()) {
      errors.customer_id = 'ID de cliente es requerido';
    }
    if (!formData.customer_type) {
      errors.customer_type = 'Tipo de cliente es requerido';
    }
    if (!formData.order_reference.trim()) {
      errors.order_reference = 'Referencia de pedido es requerida';
    }
    if (!formData.return_reason) {
      errors.return_reason = 'Motivo de devolución es requerido';
    }
    if (!formData.contact_email.trim()) {
      errors.contact_email = 'Email de contacto es requerido';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.contact_email)) {
      errors.contact_email = 'Formato de email inválido';
    }
    if (formData.items.length === 0) {
      errors.items = 'Debe añadir al menos un artículo';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  }, [formData]);

  const handleProfileSelect = useCallback((profile: 'B2C' | 'B2B') => {
    setSelectedProfile(profile);
    setFormData((prev) => ({
      ...prev,
      customer_type: profile === 'B2C' ? 'INDIVIDUAL' : 'WHOLESALER',
    }));
    setDecisionResult(null);
    setCurrentReturn(null);
    setBatchResult(null);
    setSubmitSuccess(false);
    setSubmitError(null);
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
      const { name, value } = e.target;
      setFormData((prev) => ({ ...prev, [name]: value }));
      if (formErrors[name]) {
        setFormErrors((prev) => ({ ...prev, [name]: '' }));
      }
    },
    [formErrors]
  );

  const handleItemChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const { name, value } = e.target;
      setCurrentItem((prev) => ({
        ...prev,
        [name]:
          name === 'quantity' || name === 'unit_price' || name === 'weight_kg' || name === 'volume_m3'
            ? parseFloat(value) || 0
            : value,
      }));
    },
    []
  );

  const handleAddItem = useCallback(() => {
    if (!currentItem.sku || !currentItem.product_name || !currentItem.reason_code) {
      return;
    }

    const newItem: ReturnItem = {
      sku: currentItem.sku || '',
      product_name: currentItem.product_name || '',
      quantity: currentItem.quantity || 1,
      unit_price: currentItem.unit_price || 0,
      weight_kg: currentItem.weight_kg,
      volume_m3: currentItem.volume_m3,
      reason_code: currentItem.reason_code || '',
      reason_description: currentItem.reason_description,
      condition: currentItem.condition || 'NEW',
    };

    setFormData((prev) => ({
      ...prev,
      items: [...prev.items, newItem],
    }));
    setCurrentItem({
      sku: '',
      product_name: '',
      quantity: 1,
      unit_price: 0,
      weight_kg: 0,
      volume_m3: 0,
      reason_code: '',
      condition: 'NEW',
    });
  }, [currentItem]);

  const handleRemoveItem = useCallback((index: number) => {
    setFormData((prev) => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index),
    }));
  }, []);

  const handleSubmit = useCallback(
    async (e?: React.FormEvent) => {
      if (e) e.preventDefault();
      setSubmitError(null);

      if (!validateForm()) return;

      setIsSubmitting(true);

      try {
        const returnData: ReturnRequestCreate = {
          channel: selectedProfile as ReturnChannel,
          customer_id: formData.customer_id,
          customer_type: formData.customer_type,
          order_reference: formData.order_reference,
          invoice_reference: formData.invoice_reference || undefined,
          items: formData.items,
          return_reason: formData.return_reason,
          return_reason_description: formData.return_reason_description || undefined,
          contact_email: formData.contact_email,
          contact_phone: formData.contact_phone || undefined,
        };

        const result = await returnsApi.create(returnData);

        setCurrentReturn(result);
        setDecisionResult({
          destination: result.destination!,
          return_method: result.return_method!,
          score: result.decision_score || 0,
          confidence: 0.95,
          explanation: result.decision_explanation || '',
          factors: {},
          business_rule_applied: 'RETURN_CREATED',
          requires_kam_approval: result.requires_kam_approval,
          processing_time_ms: result.processing_time_ms || 0,
        });

        setSubmitSuccess(true);
      } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : 'Error al crear la devolución';
        setSubmitError(errorMessage);
      } finally {
        setIsSubmitting(false);
      }
    },
    [selectedProfile, formData, validateForm]
  );

  const handleBatchUploadComplete = useCallback((response: BatchUploadResponse) => {
    setBatchResult(response);
  }, []);

  const handleBatchError = useCallback((error: string) => {
    setSubmitError(error);
  }, []);

  const handleDownloadQR = useCallback(() => {
    if (!currentReturn?.drop_off_qr_code) return;

    const link = document.createElement('a');
    link.href = `data:image/png;base64,${currentReturn.drop_off_qr_code}`;
    link.download = `qr-${currentReturn.return_id}.png`;
    link.click();
  }, [currentReturn]);

  const resetForm = useCallback(() => {
    setSelectedProfile(null);
    setFormData({
      customer_id: '',
      customer_type: '',
      order_reference: '',
      invoice_reference: '',
      return_reason: '',
      return_reason_description: '',
      contact_email: '',
      contact_phone: '',
      items: [],
    });
    setFormErrors({});
    setCurrentItem({
      sku: '',
      product_name: '',
      quantity: 1,
      unit_price: 0,
      weight_kg: 0,
      volume_m3: 0,
      reason_code: '',
      condition: 'NEW',
    });
    setDecisionResult(null);
    setCurrentReturn(null);
    setBatchResult(null);
    setSubmitSuccess(false);
    setSubmitError(null);
  }, []);

  const totalValue = formData.items.reduce((sum, item) => sum + item.unit_price * item.quantity, 0);
  const totalWeight = formData.items.reduce((sum, item) => sum + (item.weight_kg || 0) * item.quantity, 0);

  return (
    <div className="min-h-screen" style={{ backgroundColor: tokens.colors.pageBackground }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Portal de Devoluciones</h1>
          <p className="text-sm text-gray-500 mt-1">
            Procesa devoluciones de forma rápida y obtén decisiones automáticas
          </p>
        </div>

        {!selectedProfile && (
          <ProfileSelector
            selectedProfile={selectedProfile}
            onSelectProfile={handleProfileSelect}
          />
        )}

        {selectedProfile && (
          <div className="space-y-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div
                  className={`p-2 rounded-lg ${
                    selectedProfile === 'B2C' ? 'bg-blue-100 text-blue-600' : 'bg-purple-100 text-purple-600'
                  }`}
                >
                  {selectedProfile === 'B2C' ? <User className="w-5 h-5" /> : <Building2 className="w-5 h-5" />}
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    {selectedProfile === 'B2C' ? 'Devolución B2C' : 'Devolución B2B'}
                  </h2>
                  <p className="text-xs text-gray-500">
                    {selectedProfile === 'B2C'
                      ? 'Formulario para consumidor final'
                      : 'Portal de carga masiva para clientes corporativos'}
                  </p>
                </div>
              </div>
              <button
                onClick={resetForm}
                className="text-sm text-gray-500 hover:text-gray-700 underline"
              >
                Cambiar tipo de cliente
              </button>
            </div>

            {submitSuccess && decisionResult && (
              <div className="mb-6">
                <DecisionOutcomeCard
                  decision={decisionResult}
                  returnRequest={currentReturn}
                  onDownloadQR={handleDownloadQR}
                  showActions={true}
                />
              </div>
            )}

            {submitError && (
              <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-red-800">Error al procesar la devolución</p>
                    <p className="text-xs text-red-600 mt-1">{submitError}</p>
                  </div>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <ReturnForm
                  channel={selectedProfile}
                  formData={formData}
                  formErrors={formErrors}
                  currentItem={currentItem}
                  onInputChange={handleInputChange}
                  onItemChange={handleItemChange}
                  onAddItem={handleAddItem}
                  onRemoveItem={handleRemoveItem}
                  onSubmit={handleSubmit}
                  onCancel={resetForm}
                  isSubmitting={isSubmitting}
                />

                {selectedProfile === 'B2B' && (
                  <div className="bg-white rounded-xl border border-gray-200 p-6">
                    <h3 className="text-sm font-semibold text-gray-900 mb-4">Carga Masiva B2B</h3>
                    <p className="text-xs text-gray-500 mb-4">
                      Sube un archivo CSV con el formato: sku, quantity, reason_code, batch_id (opcional)
                    </p>
                    <BatchUploadZone
                      customerId={formData.customer_id}
                      returnReason={formData.return_reason}
                      onUploadComplete={handleBatchUploadComplete}
                      onError={handleBatchError}
                    />
                  </div>
                )}
              </div>

              <div className="space-y-6">
                <div className="bg-white rounded-xl border border-gray-200 p-6 sticky top-24">
                  <h3 className="text-sm font-semibold text-gray-900 mb-4">Resumen</h3>

                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Canal</span>
                      <StatusBadge
                        value={selectedProfile === 'B2C' ? 'B2C_USER' : 'B2B_USER'}
                        variant="status"
                        size="sm"
                      />
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Artículos</span>
                      <span className="text-sm font-medium text-gray-900">{formData.items.length}</span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Valor Total</span>
                      <span className="text-sm font-bold text-gray-900">€{totalValue.toFixed(2)}</span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Peso Total</span>
                      <span className="text-sm font-medium text-gray-900">{totalWeight.toFixed(3)} kg</span>
                    </div>

                    {selectedProfile === 'B2C' && (
                      <div className="pt-4 border-t border-gray-200">
                        <div className="bg-blue-50 rounded-lg p-3">
                          <p className="text-xs text-blue-700">
                            Para devoluciones B2C de 1-5 prendas con valor inferior a €150, se asignará Drop-off con QR.
                          </p>
                        </div>
                      </div>
                    )}

                    {selectedProfile === 'B2B' && (
                      <div className="pt-4 border-t border-gray-200">
                        <div className="bg-purple-50 rounded-lg p-3">
                          <p className="text-xs text-purple-700">
                            Las devoluciones B2B requieren autorización KAM y pickup programado.
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReturnPortalPage;
