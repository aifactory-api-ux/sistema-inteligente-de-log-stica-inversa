import React from 'react';
import { MapPin, AlertTriangle } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import type { DropOffPoint } from '../../types/models';
import { PrimaryButtonCTA } from './PrimaryButtonCTA';

interface DropOffDisplayProps {
  returnId: string;
  traceId: string;
  dropOffPoints: DropOffPoint[];
  selectedDropOff: DropOffPoint | null;
  onSelectDropOff: (point: DropOffPoint) => void;
  onDownloadQR: () => void;
}

export const DropOffDisplay: React.FC<DropOffDisplayProps> = ({
  returnId,
  traceId,
  dropOffPoints,
  selectedDropOff,
  onSelectDropOff,
  onDownloadQR,
}) => {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center gap-2 mb-6">
        <MapPin className="w-5 h-5 text-blue-500" />
        <h3 className="text-lg font-semibold text-gray-900">Entrega en Punto Drop-off</h3>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="flex flex-col items-center p-6 bg-gray-50 rounded-xl border border-gray-200">
          <p className="text-sm text-gray-500 mb-4">Código QR para Drop-off</p>
          <div id="qr-code" className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
            <QRCodeSVG
              value={`RET:${returnId}:${traceId}`}
              size={160}
              level="M"
              includeMargin
            />
          </div>
          <p className="text-xs text-gray-500 mt-4 font-mono">{returnId}</p>
          <PrimaryButtonCTA variant="outline" size="sm" onClick={onDownloadQR} className="mt-4">
            Descargar Etiqueta
          </PrimaryButtonCTA>
        </div>

        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Puntos de Entrega Cercanos</h4>
            <div className="space-y-3">
              {dropOffPoints.map((point) => (
                <div
                  key={point.point_id}
                  onClick={() => point.available && onSelectDropOff(point)}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedDropOff?.point_id === point.point_id
                      ? 'border-blue-500 bg-blue-50'
                      : point.available
                      ? 'border-gray-200 hover:border-gray-300 bg-white'
                      : 'border-gray-200 bg-gray-100 opacity-60 cursor-not-allowed'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg bg-blue-100 text-blue-600">
                        <MapPin className="w-4 h-4" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{point.name}</p>
                        <p className="text-sm text-gray-500">{point.address}</p>
                        <p className="text-xs text-gray-400 mt-1">
                          {point.available ? `Abierto: ${point.operating_hours}` : 'Cerrado temporalmente'}
                        </p>
                      </div>
                    </div>
                    {point.distance_km && (
                      <span className="text-sm font-medium text-gray-500">{point.distance_km} km</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DropOffDisplay;