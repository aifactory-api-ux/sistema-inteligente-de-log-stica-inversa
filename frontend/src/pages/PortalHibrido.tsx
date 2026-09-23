import React, { useState, useCallback } from 'react';
import { User, Building2, Package, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { tokens } from '../styles/tokens';
import { useReturnsStore } from '../stores/returnsStore';
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

const RETURN_REASONS = [
  { code: 'DEFECTIVE', label: 'Producto defectuoso' },
  { code: 'WRONG_ITEM', label: 'Producto equivocado' },
  { code: 'CHANGED_MIND', label: 'Cambio de opinión' },
  { code: 'DAMAGED', label: 'Dañado en tránsito' },
  { code: 'OTHER', label: 'Otro' },
];

const CUSTOMER_TYPES_B2C = [
  { code: 'INDIVIDUAL', label: 'Consumidor Individual' },
  { code: 'VIP', label: 'Cliente VIP' },
];

const CUSTOMER_TYPES_B2B = [
  { code: 'WHOLESALER', label: 'Mayorista' },
  { code: 'RETAILER', label: 'Cadena de Retail' },
  { code: 'CORPORATE', label: 'Corporativo' },
];

export const PortalHibrido: React.FC = () => {
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
  const [batchResult, setBatchResult] = useState<BatchUploadResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const { createReturn, currentReturn, isLoading } = useReturnsStore();

  const validateForm = (): boolean => {
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
  };

  const handleProfileSelect = (profile: 'B2C' | 'B2B') => {
    setSelectedProfile(profile);
    setFormData((prev) => ({
      ...prev,
      customer_type: profile === 'B2C' ? 'INDIVIDUAL' : 'WHOLESALER',
    }));
    setDecisionResult(null);
    setBatchResult(null);
    setSubmitSuccess(false);
    setSubmitError(null);
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (formErrors[name]) {
      setFormErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const handleItemChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setCurrentItem((prev) => ({
      ...prev,
      [name]: name === 'quantity' || name === 'unit_price' || name === 'weight_kg' || name === 'volume_m3'
        ? parseFloat(value) || 0
        : value,
    }));
  };

  const addItem = () => {
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
  };

  const removeItem = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index),
    }));
  };

  const handleSubmit = async (e?: React.FormEvent) => {
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

      const result = await createReturn(returnData);

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
  };

  const handleBatchUploadComplete = (response: BatchUploadResponse) => {
    setBatchResult(response);
  };

  const handleBatchError = (error: string) => {
    setSubmitError(error);
  };

  const handleDownloadQR = () => {
    if (!currentReturn?.drop_off_qr_code) return;

    const link = document.createElement('a');
    link.href = `data:image/png;base64,${currentReturn.drop_off_qr_code}`;
    link.download = `qr-${currentReturn.return_id}.png`;
    link.click();
  };

  const resetForm = () => {
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
    setDecisionResult(null);
    setBatchResult(null);
    setSubmitSuccess(false);
    setSubmitError(null);
  };

  const customerTypes = selectedProfile === 'B2C' ? CUSTOMER_TYPES_B2C : CUSTOMER_TYPES_B2B;

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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <button
              onClick={() => handleProfileSelect('B2C')}
              className="bg-white rounded-xl border-2 border-gray-200 p-6 hover:border-blue-500 hover:shadow-lg transition-all text-left group"
            >
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-xl bg-blue-50 text-blue-600 group-hover:bg-blue-100 transition-colors">
                  <User className="w-8 h-8" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">Consumidor B2C</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Devoluciones individuales de 1-5 prendas. Genera etiqueta QR para drop-off.
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <span className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded">Drop-off QR</span>
                    <span className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded">Reembolso rápido</span>
                  </div>
                </div>
              </div>
            </button>

            <button
              onClick={() => handleProfileSelect('B2B')}
              className="bg-white rounded-xl border-2 border-gray-200 p-6 hover:border-purple-500 hover:shadow-lg transition-all text-left group"
            >
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-xl bg-purple-50 text-purple-600 group-hover:bg-purple-100 transition-colors">
                  <Building2 className="w-8 h-8" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">Cliente Corporativo B2B</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Carga masiva de lotes. Requiere autorización KAM y pickup programado.
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <span className="px-2 py-1 text-xs bg-purple-50 text-purple-700 rounded">CSV Batch</span>
                    <span className="px-2 py-1 text-xs bg-purple-50 text-purple-700 rounded">Aprobación KAM</span>
                  </div>
                </div>
              </div>
            </button>
          </div>
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
                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <div className="flex items-center gap-2 mb-6">
                    <FileText className="w-5 h-5 text-gray-400" />
                    <h3 className="text-sm font-semibold text-gray-900">Datos del Pedido</h3>
                  </div>

                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">
                          ID Cliente *
                        </label>
                        <input
                          type="text"
                          name="customer_id"
                          value={formData.customer_id}
                          onChange={handleInputChange}
                          className={`w-full px-3 py-2 border rounded-lg text-sm ${
                            formErrors.customer_id
                              ? 'border-red-300 focus:ring-red-500'
                              : 'border-gray-300 focus:ring-blue-500'
                          }`}
                          placeholder="Ej: CLI-2024-001"
                        />
                        {formErrors.customer_id && (
                          <p className="text-xs text-red-500 mt-1">{formErrors.customer_id}</p>
                        )}
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">
                          Tipo de Cliente *
                        </label>
                        <select
                          name="customer_type"
                          value={formData.customer_type}
                          onChange={handleInputChange}
                          className={`w-full px-3 py-2 border rounded-lg text-sm ${
                            formErrors.customer_type
                              ? 'border-red-300 focus:ring-red-500'
                              : 'border-gray-300 focus:ring-blue-500'
                          }`}
                        >
                          <option value="">Seleccionar...</option>
                          {customerTypes.map((type) => (
                            <option key={type.code} value={type.code}>
                              {type.label}
                            </option>
                          ))}
                        </select>
                        {formErrors.customer_type && (
                          <p className="text-xs text-red-500 mt-1">{formErrors.customer_type}</p>
                        )}
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">
                          Referencia de Pedido *
                        </label>
                        <input
                          type="text"
                          name="order_reference"
                          value={formData.order_reference}
                          onChange={handleInputChange}
                          className={`w-full px-3 py-2 border rounded-lg text-sm ${
                            formErrors.order_reference
                              ? 'border-red-300 focus:ring-red-500'
                              : 'border-gray-300 focus:ring-blue-500'
                          }`}
                          placeholder="Ej: ORD-2024-12345"
                        />
                        {formErrors.order_reference && (
                          <p className="text-xs text-red-500 mt-1">{formErrors.order_reference}</p>
                        )}
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">
                          Referencia de Factura
                        </label>
                        <input
                          type="text"
                          name="invoice_reference"
                          value={formData.invoice_reference}
                          onChange={handleInputChange}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                          placeholder="Ej: INV-2024-67890"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">
                          Motivo de Devolución *
                        </label>
                        <select
                          name="return_reason"
                          value={formData.return_reason}
                          onChange={handleInputChange}
                          className={`w-full px-3 py-2 border rounded-lg text-sm ${
                            formErrors.return_reason
                              ? 'border-red-300 focus:ring-red-500'
                              : 'border-gray-300 focus:ring-blue-500'
                          }`}
                        >
                          <option value="">Seleccionar...</option>
                          {RETURN_REASONS.map((reason) => (
                            <option key={reason.code} value={reason.code}>
                              {reason.label}
                            </option>
                          ))}
                        </select>
                        {formErrors.return_reason && (
                          <p className="text-xs text-red-500 mt-1">{formErrors.return_reason}</p>
                        )}
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">
                          Descripción Adicional
                        </label>
                        <input
                          type="text"
                          name="return_reason_description"
                          value={formData.return_reason_description}
                          onChange={handleInputChange}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                          placeholder="Detalles adicionales..."
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">
                          Email de Contacto *
                        </label>
                        <input
                          type="email"
                          name="contact_email"
                          value={formData.contact_email}
                          onChange={handleInputChange}
                          className={`w-full px-3 py-2 border rounded-lg text-sm ${
                            formErrors.contact_email
                              ? 'border-red-300 focus:ring-red-500'
                              : 'border-gray-300 focus:ring-blue-500'
                          }`}
                          placeholder="cliente@ejemplo.com"
                        />
                        {formErrors.contact_email && (
                          <p className="text-xs text-red-500 mt-1">{formErrors.contact_email}</p>
                        )}
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">
                          Teléfono de Contacto
                        </label>
                        <input
                          type="tel"
                          name="contact_phone"
                          value={formData.contact_phone}
                          onChange={handleInputChange}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                          placeholder="+34 600 000 000"
                        />
                      </div>
                    </div>
                  </form>
                </div>

                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <div className="flex items-center gap-2 mb-6">
                    <Package className="w-5 h-5 text-gray-400" />
                    <h3 className="text-sm font-semibold text-gray-900">Artículos a Devolver</h3>
                  </div>

                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-6 gap-3">
                      <div className="md:col-span-2">
                        <label className="block text-xs font-medium text-gray-500 mb-1">SKU *</label>
                        <input
                          type="text"
                          name="sku"
                          value={currentItem.sku || ''}
                          onChange={handleItemChange}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                          placeholder="SKU-001"
                        />
                      </div>
                      <div className="md:col-span-2">
                        <label className="block text-xs font-medium text-gray-500 mb-1">Producto *</label>
                        <input
                          type="text"
                          name="product_name"
                          value={currentItem.product_name || ''}
                          onChange={handleItemChange}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                          placeholder="Nombre del producto"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Cantidad *</label>
                        <input
                          type="number"
                          name="quantity"
                          value={currentItem.quantity || 1}
                          onChange={handleItemChange}
                          min="1"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Precio Unit. *</label>
                        <input
                          type="number"
                          name="unit_price"
                          value={currentItem.unit_price || 0}
                          onChange={handleItemChange}
                          step="0.01"
                          min="0"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Peso (kg)</label>
                        <input
                          type="number"
                          name="weight_kg"
                          value={currentItem.weight_kg || 0}
                          onChange={handleItemChange}
                          step="0.001"
                          min="0"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Volumen (m³)</label>
                        <input
                          type="number"
                          name="volume_m3"
                          value={currentItem.volume_m3 || 0}
                          onChange={handleItemChange}
                          step="0.0001"
                          min="0"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Estado</label>
                        <select
                          name="condition"
                          value={currentItem.condition || 'NEW'}
                          onChange={handleItemChange}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                        >
                          <option value="NEW">Nuevo</option>
                          <option value="OPENED">Abierto</option>
                          <option value="DAMAGED">Dañado</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Motivo *</label>
                        <select
                          name="reason_code"
                          value={currentItem.reason_code || ''}
                          onChange={handleItemChange}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                        >
                          <option value="">Seleccionar...</option>
                          {RETURN_REASONS.map((reason) => (
                            <option key={reason.code} value={reason.code}>
                              {reason.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={addItem}
                      disabled={!currentItem.sku || !currentItem.product_name || !currentItem.reason_code}
                      className="w-full md:w-auto px-4 py-2 text-sm font-medium text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      + Añadir Artículo
                    </button>

                    {formErrors.items && (
                      <p className="text-xs text-red-500">{formErrors.items}</p>
                    )}

                    {formData.items.length > 0 && (
                      <div className="mt-4 border rounded-lg overflow-hidden">
                        <table className="w-full text-sm">
                          <thead style={{ backgroundColor: tokens.colors.gray50 }}>
                            <tr>
                              <th className="px-4 py-2 text-left font-medium text-gray-600">SKU</th>
                              <th className="px-4 py-2 text-left font-medium text-gray-600">Producto</th>
                              <th className="px-4 py-2 text-center font-medium text-gray-600">Cant.</th>
                              <th className="px-4 py-2 text-right font-medium text-gray-600">Precio</th>
                              <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
                              <th className="px-4 py-2 text-left font-medium text-gray-600">Motivo</th>
                              <th className="px-4 py-2"></th>
                            </tr>
                          </thead>
                          <tbody>
                            {formData.items.map((item, index) => (
                              <tr key={index} className="border-t">
                                <td className="px-4 py-2 font-mono text-xs">{item.sku}</td>
                                <td className="px-4 py-2">{item.product_name}</td>
                                <td className="px-4 py-2 text-center">{item.quantity}</td>
                                <td className="px-4 py-2 text-right">€{item.unit_price.toFixed(2)}</td>
                                <td className="px-4 py-2">
                                  <StatusBadge value={item.condition} size="sm" />
                                </td>
                                <td className="px-4 py-2 text-xs text-gray-500">{item.reason_code}</td>
                                <td className="px-4 py-2">
                                  <button
                                    type="button"
                                    onClick={() => removeItem(index)}
                                    className="text-red-500 hover:text-red-700 text-xs"
                                  >
                                    Eliminar
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                          <tfoot style={{ backgroundColor: tokens.colors.gray50 }}>
                            <tr>
                              <td colSpan={3} className="px-4 py-2 font-medium text-gray-700">
                                Total ({formData.items.length} artículos)
                              </td>
                              <td className="px-4 py-2 text-right font-bold text-gray-900">
                                €{formData.items.reduce((sum, item) => sum + item.unit_price * item.quantity, 0).toFixed(2)}
                              </td>
                              <td colSpan={3}></td>
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    )}
                  </div>
                </div>

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

                <div className="flex justify-end gap-3 pt-4">
                  <PrimaryButtonCTA
                    variant="outline"
                    onClick={resetForm}
                    disabled={isSubmitting}
                  >
                    Cancelar
                  </PrimaryButtonCTA>
                  <PrimaryButtonCTA
                    variant="solid"
                    onClick={handleSubmit}
                    loading={isSubmitting}
                    disabled={isSubmitting || formData.items.length === 0}
                  >
                    {isSubmitting ? 'Procesando...' : 'Procesar Devolución'}
                  </PrimaryButtonCTA>
                </div>
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
                      <span className="text-sm font-bold text-gray-900">
                        €{formData.items.reduce((sum, item) => sum + item.unit_price * item.quantity, 0).toFixed(2)}
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Peso Total</span>
                      <span className="text-sm font-medium text-gray-900">
                        {formData.items.reduce((sum, item) => sum + (item.weight_kg || 0) * item.quantity, 0).toFixed(3)} kg
                      </span>
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

export default PortalHibrido;
