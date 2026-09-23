import React from 'react';
import { FileText, Package, AlertCircle } from 'lucide-react';
import { tokens } from '../../styles/tokens';
import { PrimaryButtonCTA } from './PrimaryButtonCTA';
import { StatusBadge } from './StatusBadge';
import type { ReturnItem } from '../../types/models';

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

interface ReturnFormProps {
  channel: 'B2C' | 'B2B';
  formData: FormData;
  formErrors: FormErrors;
  currentItem: Partial<ReturnItem>;
  onInputChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => void;
  onItemChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
  onAddItem: () => void;
  onRemoveItem: (index: number) => void;
  onSubmit: (e?: React.FormEvent) => void;
  onCancel: () => void;
  isSubmitting: boolean;
}

export const ReturnForm: React.FC<ReturnFormProps> = ({
  channel,
  formData,
  formErrors,
  currentItem,
  onInputChange,
  onItemChange,
  onAddItem,
  onRemoveItem,
  onSubmit,
  onCancel,
  isSubmitting,
}) => {
  const customerTypes = channel === 'B2C' ? CUSTOMER_TYPES_B2C : CUSTOMER_TYPES_B2B;

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-6">
          <FileText className="w-5 h-5 text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-900">Datos del Pedido</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              ID Cliente *
            </label>
            <input
              type="text"
              name="customer_id"
              value={formData.customer_id}
              onChange={onInputChange}
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
              onChange={onInputChange}
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
              onChange={onInputChange}
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
              onChange={onInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              placeholder="Ej: INV-2024-67890"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Motivo de Devolución *
            </label>
            <select
              name="return_reason"
              value={formData.return_reason}
              onChange={onInputChange}
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
              onChange={onInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              placeholder="Detalles adicionales..."
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Email de Contacto *
            </label>
            <input
              type="email"
              name="contact_email"
              value={formData.contact_email}
              onChange={onInputChange}
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
              onChange={onInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              placeholder="+34 600 000 000"
            />
          </div>
        </div>
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
                onChange={onItemChange}
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
                onChange={onItemChange}
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
                onChange={onItemChange}
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
                onChange={onItemChange}
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
                onChange={onItemChange}
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
                onChange={onItemChange}
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
                onChange={onItemChange}
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
                onChange={onItemChange}
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
            onClick={onAddItem}
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
                          onClick={() => onRemoveItem(index)}
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

      <div className="flex justify-end gap-3 pt-4">
        <PrimaryButtonCTA
          variant="outline"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancelar
        </PrimaryButtonCTA>
        <PrimaryButtonCTA
          variant="solid"
          type="submit"
          onClick={onSubmit}
          loading={isSubmitting}
          disabled={isSubmitting || formData.items.length === 0}
        >
          {isSubmitting ? 'Procesando...' : 'Procesar Devolución'}
        </PrimaryButtonCTA>
      </div>
    </form>
  );
};

export default ReturnForm;
