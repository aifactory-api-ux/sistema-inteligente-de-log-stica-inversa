import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Bell, User, LogOut, Settings } from 'lucide-react';
import { tokens } from '../../styles/tokens';
import { useAuthStore } from '../../stores/authStore';
import { useControlTowerStore } from '../../stores/controlTowerStore';

export const AppNavigationHeader: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, isAuthenticated } = useAuthStore();
  const { unreadAlertCount } = useControlTowerStore();

  const getCurrentPage = (): string => {
    const path = location.pathname;
    if (path === '/') return 'portal';
    if (path.startsWith('/logistics')) return 'logistics';
    if (path.startsWith('/control-tower')) return 'control-tower';
    return 'portal';
  };

  const currentPage = getCurrentPage();

  const navItems = [
    { id: 'portal', label: 'Portal Devoluciones', path: '/' },
    { id: 'logistics', label: 'Módulo Logístico', path: '/logistics' },
    { id: 'control-tower', label: 'Torre de Control', path: '/control-tower' },
  ];

  const handleNavigate = (path: string) => {
    navigate(path);
  };

  const getRoleLabel = (role: string): string => {
    const roleLabels: Record<string, string> = {
      B2C_USER: 'Consumidor',
      B2B_USER: 'Cliente Corporativo',
      SUPERVISOR: 'Supervisor',
      KAM: 'Key Account Manager',
      ADMIN: 'Administrador',
    };
    return roleLabels[role] || role;
  };

  const getRoleBadgeColor = (role: string): string => {
    const roleColors: Record<string, string> = {
      B2C_USER: '#DBEAFE',
      B2B_USER: '#E0E7FF',
      SUPERVISOR: '#D1FAE5',
      KAM: '#FED7AA',
      ADMIN: '#FEE2E2',
    };
    return roleColors[role] || '#F3F4F6';
  };

  return (
    <header
      className="sticky top-0 z-50 border-b"
      style={{
        backgroundColor: tokens.colors.darkNavy,
        borderColor: tokens.colors.gray800,
      }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="white"
                  strokeWidth="2"
                  className="w-5 h-5"
                >
                  <path d="M9 17H7A5 5 0 0 1 7 7h2" />
                  <path d="M15 7h2a5 5 0 1 1 0 10h-2" />
                  <line x1="8" y1="12" x2="16" y2="12" />
                </svg>
              </div>
              <div>
                <h1 className="text-sm font-semibold text-white">Logística Inversa</h1>
                <p className="text-xs text-gray-400">Módulo Inteligente</p>
              </div>
            </div>

            <nav className="hidden md:flex items-center gap-1">
              {navItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => handleNavigate(item.path)}
                  className={`
                    px-3 py-2 text-sm font-medium rounded-lg transition-colors
                    ${currentPage === item.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:text-white hover:bg-gray-700'
                    }
                  `}
                >
                  {item.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <button
              className="relative p-2 text-gray-400 hover:text-white transition-colors"
              aria-label="Notificaciones"
            >
              <Bell className="w-5 h-5" />
              {unreadAlertCount > 0 && (
                <span
                  className="absolute top-1 right-1 w-4 h-4 text-xs font-bold text-white rounded-full flex items-center justify-center"
                  style={{ backgroundColor: tokens.colors.danger }}
                >
                  {unreadAlertCount > 9 ? '9+' : unreadAlertCount}
                </span>
              )}
            </button>

            {isAuthenticated && user ? (
              <div className="flex items-center gap-3 pl-3 border-l border-gray-700">
                <div className="hidden sm:block text-right">
                  <p className="text-sm font-medium text-white">{user.username}</p>
                  <span
                    className="inline-block px-2 py-0.5 text-xs font-medium rounded"
                    style={{
                      backgroundColor: getRoleBadgeColor(user.role),
                      color: tokens.colors.gray800,
                    }}
                  >
                    {getRoleLabel(user.role)}
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    className="p-2 text-gray-400 hover:text-white transition-colors"
                    aria-label="Configuración"
                  >
                    <Settings className="w-4 h-4" />
                  </button>
                  <button
                    onClick={logout}
                    className="p-2 text-gray-400 hover:text-white transition-colors"
                    aria-label="Cerrar sesión"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ) : (
              <button className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-300 hover:text-white border border-gray-600 rounded-lg hover:border-gray-500 transition-colors">
                <User className="w-4 h-4" />
                <span>Iniciar Sesión</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {currentPage && (
        <div className="md:hidden border-t border-gray-700 px-4 py-2">
          <div className="flex gap-2 overflow-x-auto">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => handleNavigate(item.path)}
                className={`
                  px-3 py-1.5 text-xs font-medium rounded-lg whitespace-nowrap transition-colors
                  ${currentPage === item.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:text-white hover:bg-gray-700'
                  }
                `}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </header>
  );
};
