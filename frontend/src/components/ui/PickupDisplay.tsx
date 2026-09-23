import React from 'react';
import { Truck, CheckCircle } from 'lucide-react';
import { PrimaryButtonCTA } from './PrimaryButtonCTA';
import type { PickupSlot, Address } from '../../types/models';

interface PickupFormData {
  address: Address;
  preferred_date: string;
  preferred_time_slot: string;
  contact_phone: string;
  special_instructions: string;
}

interface PickupDisplayProps {
  returnId?: string;
  pickupSlots: PickupSlot[];
  pickupForm: PickupFormData;
  pickupScheduled: boolean;
  isScheduling: boolean;
  onFormChange: (name: string, value: string) => void;
  onSchedule: () => void;
}

export const PickupDisplay: React.FC<PickupDisplayProps> = ({
  pickupSlots,
  pickupForm,
  pickupScheduled,
  isScheduling,
  onFormChange,
  onSchedule,
}) => {
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    onFormChange(e.target.name, e.target.value);
  };

  if (pickupScheduled) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-6">
          <CheckCircle className="w-5 h-5 text-emerald-500" />
          <h3 className="text-lg font-semibold text-gray-900">Recogida Programada</h3>
        </div>

        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6 text-center">
          <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-emerald-500" />
          </div>
          <h4 className="text-lg font-semibold text-emerald-800">¡Recogida Programada!</h4>
          <p className="text-sm text-emerald-600 mt-2">
            Un transportista recogerá el paquete en la dirección indicada.
          </p>
          <div className="mt-4 pt-4 border-t border-emerald-200">
            <p className="text-sm text-emerald-700">
              <strong>Fecha:</strong> {pickupForm.preferred_date}
            </p>
            <p className="text-sm text-emerald-700">
              <strong>Horario:</strong> {pickupForm.preferred_time_slot}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center gap-2 mb-6">
        <Truck className="w-5 h-5 text-indigo-500" />
        <h3 className="text-lg font-semibold text-gray-900">Programar Recogida</h3>
      </div>

      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-gray-500 mb-1">Dirección de Recogida *</label>
            <input
              type="text"
              name="address.street"
              value={pickupForm.address.street}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              placeholder="Calle, número, piso"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Ciudad *</label>
            <input
              type="text"
              name="address.city"
              value={pickupForm.address.city}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              placeholder="Madrid"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Código Postal *</label>
            <input
              type="text"
              name="address.postal_code"
              value={pickupForm.address.postal_code}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              placeholder="28001"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Teléfono de Contacto</label>
            <input
              type="tel"
              name="contact_phone"
              value={pickupForm.contact_phone}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              placeholder="+34 600 000 000"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Fecha Preferida *</label>
            <input
              type="date"
              name="preferred_date"
              value={pickupForm.preferred_date}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              min={new Date().toISOString().split('T')[0]}
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-gray-500 mb-1">Franja Horaria *</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {pickupSlots
                .filter((slot) => slot.available && slot.date === pickupForm.preferred_date)
                .map((slot) => (
                  <button
                    key={slot.slot_id}
                    type="button"
                    onClick={() => onFormChange('preferred_time_slot', slot.time_slot)}
                    className={`px-3 py-2 text-sm rounded-lg border transition-all ${
                      pickupForm.preferred_time_slot === slot.time_slot
                        ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                        : 'border-gray-200 hover:border-gray-300 bg-white text-gray-700'
                    }`}
                  >
                    {slot.time_slot}
                  </button>
                ))}
              {pickupSlots.filter((slot) => slot.available && slot.date === pickupForm.preferred_date)
                .length === 0 && (
                <p className="text-sm text-gray-500 col-span-4 py-2">
                  Selecciona una fecha para ver franjas disponibles
                </p>
              )}
            </div>
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-gray-500 mb-1">Instrucciones Especiales</label>
            <textarea
              name="special_instructions"
              value={pickupForm.special_instructions}
              onChange={handleInputChange}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              placeholder="Indicaciones para el transportista..."
            />
          </div>
        </div>

        <div className="flex justify-end">
          <PrimaryButtonCTA
            variant="solid"
            onClick={onSchedule}
            loading={isScheduling}
            disabled={
              !pickupForm.address.street ||
              !pickupForm.address.city ||
              !pickupForm.preferred_date ||
              !pickupForm.preferred_time_slot
            }
          >
            Confirmar Programación
          </PrimaryButtonCTA>
        </div>
      </div>
    </div>
  );
};

export default PickupDisplay;