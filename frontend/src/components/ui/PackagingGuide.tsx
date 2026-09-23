import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface PackagingGuideProps {
  compact?: boolean;
}

export const PackagingGuide: React.FC<PackagingGuideProps> = ({ compact = false }) => {
  const guidelines = [
    'Utiliza el embalaje original o uno similar en buenas condiciones',
    'Asegura que todos los artículos estén protegidos individualmente',
    'Incluye una copia de la etiqueta QR en el exterior del paquete',
    'Sella el paquete correctamente con cinta adhesiva resistente',
    'Verifica que el peso no supere los límites permitidos por el punto de entrega',
  ];

  if (compact) {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
        <div className="flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-medium text-amber-800">Directrices de Embalaje</p>
            <ul className="text-xs text-amber-700 mt-1 space-y-0.5">
              {guidelines.slice(0, 3).map((g, i) => (
                <li key={i}>• {g}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-amber-500" />
        <h3 className="text-lg font-semibold text-gray-900">Directrices de Embalaje</h3>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <ul className="space-y-3">
          {guidelines.map((guideline, index) => (
            <li key={index} className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-amber-200 text-amber-800 text-xs font-medium flex items-center justify-center">
                {index + 1}
              </span>
              <span className="text-sm text-amber-800">{guideline}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          <strong className="text-gray-700">Nota:</strong> El incumplimiento de las directrices de embalaje puede retrasar el procesamiento de tu devolución.
        </p>
      </div>
    </div>
  );
};

export default PackagingGuide;