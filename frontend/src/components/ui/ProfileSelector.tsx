import { User, Building2 } from 'lucide-react';
import { tokens } from '../../styles/tokens';

export interface ProfileOption {
  id: 'B2C' | 'B2B';
  label: string;
  description: string;
  icon: React.ReactNode;
  features: string[];
  color: string;
  bgColor: string;
}

const B2C_PROFILE: ProfileOption = {
  id: 'B2C',
  label: 'Consumidor B2C',
  description: 'Devoluciones individuales de 1-5 prendas. Genera etiqueta QR para drop-off.',
  icon: <User className="w-8 h-8" />,
  features: ['Drop-off QR', 'Reembolso rápido', '1-5 prendas'],
  color: '#2563EB',
  bgColor: '#DBEAFE',
};

const B2B_PROFILE: ProfileOption = {
  id: 'B2B',
  label: 'Cliente Corporativo B2B',
  description: 'Carga masiva de lotes. Requiere autorización KAM y pickup programado.',
  icon: <Building2 className="w-8 h-8" />,
  features: ['CSV Batch', 'Aprobación KAM', 'Lotes masivos'],
  color: '#7C3AED',
  bgColor: '#EDE9FE',
};

interface ProfileSelectorProps {
  selectedProfile: 'B2C' | 'B2B' | null;
  onSelectProfile: (profile: 'B2C' | 'B2B') => void;
}

export const ProfileSelector: React.FC<ProfileSelectorProps> = ({
  selectedProfile,
  onSelectProfile,
}) => {
  const profiles = [B2C_PROFILE, B2B_PROFILE];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      {profiles.map((profile) => {
        const isSelected = selectedProfile === profile.id;
        return (
          <button
            key={profile.id}
            onClick={() => onSelectProfile(profile.id)}
            className={`
              bg-white rounded-xl border-2 p-6 hover:shadow-lg transition-all text-left group
              ${isSelected ? 'border-blue-500 shadow-lg' : 'border-gray-200 hover:border-blue-400'}
            `}
            style={{
              borderColor: isSelected ? profile.color : undefined,
            }}
          >
            <div className="flex items-start gap-4">
              <div
                className="p-3 rounded-xl transition-colors"
                style={{
                  backgroundColor: profile.bgColor,
                  color: profile.color,
                }}
              >
                {profile.icon}
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900">{profile.label}</h3>
                <p className="text-sm text-gray-500 mt-1">{profile.description}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {profile.features.map((feature) => (
                    <span
                      key={feature}
                      className="px-2 py-1 text-xs rounded"
                      style={{
                        backgroundColor: profile.bgColor,
                        color: profile.color,
                      }}
                    >
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
};

export default ProfileSelector;
