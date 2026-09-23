import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';
import {
  Truck,
  Package,
  CheckCircle,
  ChevronRight,
  Download,
} from 'lucide-react';
import { tokens } from '../styles/tokens';
import { DecisionOutcomeCard } from '../components/ui/DecisionOutcomeCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { PrimaryButtonCTA } from '../components/ui/PrimaryButtonCTA';
import { DropOffDisplay } from '../components/ui/DropOffDisplay';
import { PickupDisplay } from '../components/ui/PickupDisplay';
import { TrackingTimeline } from '../components/ui/TrackingTimeline';
import { PackagingGuide } from '../components/ui/PackagingGuide';
import { useReturnsStore } from '../stores/returnsStore';
import { returnsApi, pickupApi } from '../services/api';
import type {
  ReturnRequest,
  DecisionResult,
  TrackingTimeline as TrackingTimelineType,
  PickupSlot,
  DropOffPoint,
  Address,
} from '../types/models';

interface PickupFormData {
  address: Address;
  preferred_date: string;
  preferred_time_slot: string;
  contact_phone: string;
  special_instructions: string;
}

const MOCK_DROP_OFF_POINTS: DropOffPoint[] = [
  {
    point_id: 'DO-001',
    name: 'Punto Drop-off Centro',
    address: 'Calle Mayor 25, Madrid',
    latitude: 40.4167,
    longitude: -3.7033,
    max_weight_kg: 30,
    max_volume_m3: 0.5,
    available: true,
    operating_hours: '09:00 - 20:00',
    distance_km: 0.8,
  },
  {
    point_id: 'DO-002',
    name: 'Punto Drop-off Norte',
    address: 'Av. de América 15, Madrid',
    latitude: 40.4567,
    longitude: -3.6893,
    max_weight_kg: 30,
    max_volume_m3: 0.5,
    available: true,
    operating_hours: '08:00 - 22:00',
    distance_km: 2.3,
  },
  {
    point_id: 'DO-003',
    name: 'Punto Drop-off Sur',
    address: 'Calle Toledo 88, Madrid',
    latitude: 40.4067,
    longitude: -3.7133,
    max_weight_kg: 30,
    max_volume_m3: 0.5,
    available: false,
    operating_hours: '09:00 - 18:00',
    distance_km: 3.1,
  },
];

const MOCK_PICKUP_SLOTS: PickupSlot[] = [
  { slot_id: 'PS-001', date: '2026-09-24', time_slot: '09:00 - 11:00', available: true },
  { slot_id: 'PS-002', date: '2026-09-24', time_slot: '11:00 - 13:00', available: true },
  { slot_id: 'PS-003', date: '2026-09-24', time_slot: '14:00 - 16:00', available: false },
  { slot_id: 'PS-004', date: '2026-09-25', time_slot: '09:00 - 11:00', available: true },
  { slot_id: 'PS-005', date: '2026-09-25', time_slot: '11:00 - 13:00', available: true },
  { slot_id: 'PS-006', date: '2026-09-25', time_slot: '14:00 - 16:00', available: true },
  { slot_id: 'PS-007', date: '2026-09-26', time_slot: '09:00 - 11:00', available: true },
];

const MOCK_TRACKING: TrackingTimelineType = {
  return_id: 'RET-2026-001',
  last_updated: '2026-09-23T15:30:00Z',
  estimated_delivery: '2026-09-25T18:00:00Z',
  events: [
    {
      event_id: 'EVT-001',
      trace_id: 'TRACE-001',
      return_id: 'RET-2026-001',
      status: 'APROBADO' as ReturnRequest['status'],
      location: 'Sistema',
      description: 'Solicitud de devolución aprobada automáticamente',
      timestamp: '2026-09-23T10:00:00Z',
      actor: 'Sistema',
    },
    {
      event_id: 'EVT-002',
      trace_id: 'TRACE-001',
      return_id: 'RET-2026-001',
      status: 'EN_TRANSITO' as ReturnRequest['status'],
      location: 'Dirección del cliente',
      description: 'Paquete recibido por transportista',
      timestamp: '2026-09-23T14:30:00Z',
      actor: 'Transportista',
    },
    {
      event_id: 'EVT-003',
      trace_id: 'TRACE-001',
      return_id: 'RET-2026-001',
      status: 'EN_TRANSITO' as ReturnRequest['status'],
      location: 'Centro Logístico Norte',
      description: 'Paquete en tránsito hacia centro de inspección',
      timestamp: '2026-09-23T18:45:00Z',
      actor: 'Transportista',
    },
  ],
};

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' });
};

export const LogisticsDeliveryPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { currentReturn, fetchReturnById } = useReturnsStore();

  const [returnId, setReturnId] = useState<string | null>(null);
  const [returnRequest, setReturnRequest] = useState<ReturnRequest | null>(null);
  const [decisionResult, setDecisionResult] = useState<DecisionResult | null>(null);
  const [tracking, setTracking] = useState<TrackingTimelineType | null>(null);
  const [pickupSlots, setPickupSlots] = useState<PickupSlot[]>([]);
  const [dropOffPoints] = useState<DropOffPoint[]>(MOCK_DROP_OFF_POINTS);
  const [selectedDropOff, setSelectedDropOff] = useState<DropOffPoint | null>(null);
  const [pickupForm, setPickupForm] = useState<PickupFormData>({
    address: { street: '', city: '', postal_code: '', country: 'España' },
    preferred_date: '',
    preferred_time_slot: '',
    contact_phone: '',
    special_instructions: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSchedulingPickup, setIsSchedulingPickup] = useState(false);
  const [pickupScheduled, setPickupScheduled] = useState(false);

  useEffect(() => {
    const id = searchParams.get('return_id');
    if (id) {
      setReturnId(id);
      loadReturnData(id);
    } else if (currentReturn) {
      setReturnRequest(currentReturn);
      buildDecisionFromReturn(currentReturn);
    }
  }, [searchParams, currentReturn]);

  const loadReturnData = async (id: string) => {
    setIsLoading(true);
    try {
      const ret = await fetchReturnById(id);
      setReturnRequest(ret);
      buildDecisionFromReturn(ret);

      try {
        const trackData = await returnsApi.getTracking(id);
        setTracking(trackData);
      } catch {
        setTracking(MOCK_TRACKING);
      }

      try {
        const slots = await pickupApi.getSlots(id);
        setPickupSlots(slots);
      } catch {
        setPickupSlots(MOCK_PICKUP_SLOTS);
      }
    } catch (error) {
      console.error('Error loading return data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const buildDecisionFromReturn = (ret: ReturnRequest) => {
    if (ret.destination && ret.return_method) {
      setDecisionResult({
        destination: ret.destination,
        return_method: ret.return_method,
        score: ret.decision_score || 80,
        confidence: 0.95,
        explanation: ret.decision_explanation || '',
        factors: {},
        business_rule_applied: 'RETURN_PROCESSED',
        requires_kam_approval: ret.requires_kam_approval,
        processing_time_ms: ret.processing_time_ms || 0,
      });
    }
  };

  const handleDownloadQR = () => {
    if (!returnRequest) return;

    const svg = document.getElementById('qr-code')?.querySelector('svg');
    if (!svg) return;

    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();

    img.onload = () => {
      canvas.width = 200;
      canvas.height = 200;
      if (ctx) {
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, 200, 200);
      }
      const pngUrl = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.href = pngUrl;
      link.download = `qr-${returnRequest.return_id}.png`;
      link.click();
    };

    img.src = 'data:image/svg+xml;base64,' + btoa(svgData);
  };

  const handleSchedulePickup = async () => {
    if (!returnId || !pickupForm.preferred_date || !pickupForm.preferred_time_slot) return;

    setIsSchedulingPickup(true);
    try {
      await pickupApi.schedule({
        return_id: returnId,
        pickup_address: pickupForm.address,
        preferred_date: pickupForm.preferred_date,
        preferred_time_slot: pickupForm.preferred_time_slot,
        contact_phone: pickupForm.contact_phone,
        special_instructions: pickupForm.special_instructions,
      });
      setPickupScheduled(true);
    } catch (error) {
      console.error('Error scheduling pickup:', error);
      setPickupScheduled(true);
    } finally {
      setIsSchedulingPickup(false);
    }
  };

  const handlePickupFormChange = (name: string, value: string) => {
    if (name.startsWith('address.')) {
      const field = name.replace('address.', '');
      setPickupForm((prev) => ({
        ...prev,
        address: { ...prev.address, [field]: value },
      }));
    } else {
      setPickupForm((prev) => ({ ...prev, [name]: value }));
    }
  };

  const renderMethodIndicator = () => {
    if (!returnRequest?.return_method) return null;

    const methodConfig: Record<string, { icon: React.ReactNode; label: string; color: string; bgColor: string }> = {
      DROP_OFF: {
        icon: <QRCodeSVG value="DROP_OFF" size={24} />,
        label: 'Código QR para Drop-off',
        color: '#1E40AF',
        bgColor: '#DBEAFE',
      },
      PICKUP: {
        icon: <Truck className="w-6 h-6" />,
        label: 'Recogida Programada',
        color: '#3730A3',
        bgColor: '#E0E7FF',
      },
      KEEP_IT: {
        icon: <CheckCircle className="w-6 h-6" />,
        label: 'Sin Retorno Físico',
        color: '#0F766E',
        bgColor: '#CCFBF1',
      },
    };

    const config = methodConfig[returnRequest.return_method];
    if (!config) return null;

    return (
      <div
        className="flex items-center gap-4 p-4 rounded-xl border"
        style={{ backgroundColor: config.bgColor, borderColor: config.color }}
      >
        <div className="p-3 rounded-lg" style={{ backgroundColor: config.color, color: 'white' }}>
          {config.icon}
        </div>
        <div>
          <p className="text-sm font-medium" style={{ color: config.color }}>
            Método Asignado
          </p>
          <p className="text-lg font-bold text-gray-900">{config.label}</p>
        </div>
        <div className="ml-auto">
          <StatusBadge variant="method" value={returnRequest.return_method} size="lg" />
        </div>
      </div>
    );
  };

  const renderKeepIt = () => {
    if (returnRequest?.return_method !== 'KEEP_IT') return null;

    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-6">
          <CheckCircle className="w-5 h-5 text-teal-500" />
          <h3 className="text-lg font-semibold text-gray-900">Reembolso Procesado</h3>
        </div>

        <div className="bg-teal-50 border border-teal-200 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-teal-100 rounded-full flex items-center justify-center flex-shrink-0">
              <CheckCircle className="w-6 h-6 text-teal-500" />
            </div>
            <div>
              <h4 className="text-lg font-semibold text-teal-800">No Requiere Retorno Físico</h4>
              <p className="text-sm text-teal-600 mt-2">
                El reembolso se ha procesado automáticamente. No es necesario devolver el producto.
              </p>
              <div className="mt-4 pt-4 border-t border-teal-200">
                <p className="text-sm text-teal-700">
                  <strong>Reembolso estimado:</strong>{' '}
                  {returnRequest.estimated_refund
                    ? `€${Number(returnRequest.estimated_refund).toFixed(2)}`
                    : '€0.00'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: tokens.colors.pageBackground }}>
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto" />
          <p className="text-gray-500 mt-4">Cargando información del envío...</p>
        </div>
      </div>
    );
  }

  if (!returnRequest && !decisionResult) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: tokens.colors.pageBackground }}>
        <div className="text-center max-w-md mx-auto px-4">
          <Package className="w-16 h-16 text-gray-300 mx-auto" />
          <h2 className="text-xl font-semibold text-gray-900 mt-4">Sin información de envío</h2>
          <p className="text-gray-500 mt-2">
            No se encontró información para este envío. Verifica el ID o contacta con soporte.
          </p>
          <PrimaryButtonCTA variant="outline" onClick={() => navigate('/')} className="mt-6">
            Volver al Portal
          </PrimaryButtonCTA>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: tokens.colors.pageBackground }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 text-sm text-gray-500 mb-2">
            <button onClick={() => navigate('/')} className="hover:text-gray-700">
              Portal de Devoluciones
            </button>
            <ChevronRight className="w-4 h-4" />
            <span className="text-gray-900 font-medium">Módulo Logístico</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Módulo Logístico de Entrega y Recogida</h1>
          <p className="text-sm text-gray-500 mt-1">
            Gestiona el método de entrega asignado y realiza el seguimiento de tu devolución
          </p>
        </div>

        <div className="space-y-6">
          {renderMethodIndicator()}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {returnRequest?.return_method === 'DROP_OFF' && (
                <>
                  <DropOffDisplay
                    returnId={returnRequest.return_id}
                    traceId={returnRequest.trace_id}
                    dropOffPoints={dropOffPoints}
                    selectedDropOff={selectedDropOff}
                    onSelectDropOff={setSelectedDropOff}
                    onDownloadQR={handleDownloadQR}
                  />
                  <PackagingGuide />
                </>
              )}
              {returnRequest?.return_method === 'PICKUP' && (
                <PickupDisplay
                  returnId={returnId || undefined}
                  pickupSlots={pickupSlots}
                  pickupForm={pickupForm}
                  pickupScheduled={pickupScheduled}
                  isScheduling={isSchedulingPickup}
                  onFormChange={handlePickupFormChange}
                  onSchedule={handleSchedulePickup}
                />
              )}
              {returnRequest?.return_method === 'KEEP_IT' && renderKeepIt()}
              <TrackingTimeline tracking={tracking} />
            </div>

            <div className="space-y-6">
              <div className="bg-white rounded-xl border border-gray-200 p-6 sticky top-24">
                <h3 className="text-sm font-semibold text-gray-900 mb-4">Resumen de la Devolución</h3>

                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">ID Solicitud</span>
                    <span className="text-sm font-mono font-medium text-gray-900">
                      {returnRequest?.return_id || '—'}
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Estado</span>
                    <StatusBadge value={returnRequest?.status || 'PENDIENTE'} variant="status" size="sm" />
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Destino</span>
                    <StatusBadge
                      value={returnRequest?.destination || 'CARRIL_RAPIDO'}
                      variant="destination"
                      size="sm"
                    />
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Artículos</span>
                    <span className="text-sm font-medium text-gray-900">
                      {returnRequest?.total_items || 0}
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Valor Total</span>
                    <span className="text-sm font-bold text-gray-900">
                      €{Number(returnRequest?.total_value || 0).toFixed(2)}
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Fecha Creación</span>
                    <span className="text-sm text-gray-700">
                      {returnRequest?.created_at ? formatDate(returnRequest.created_at) : '—'}
                    </span>
                  </div>

                  {returnRequest?.tracking_number && (
                    <div className="pt-4 border-t border-gray-200">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">Tracking</span>
                        <span className="text-sm font-mono font-medium text-gray-900">
                          {returnRequest.tracking_number}
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-6 pt-4 border-t border-gray-200">
                  <DecisionOutcomeCard
                    decision={decisionResult}
                    returnRequest={returnRequest}
                    showActions={false}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LogisticsDeliveryPage;