interface AppConfig {
  apiBaseUrl: string;
  apiVersion: string;
  appVersion: string;
  environment: 'development' | 'production' | 'staging';
  buildTimestamp: string;
}

interface FeatureFlags {
  enableRealtimeUpdates: boolean;
  enableBatchUpload: boolean;
  enableQRDownload: boolean;
  enableKPIPolling: boolean;
  kpiRefreshIntervalMs: number;
}

const getEnvVariable = (key: string, fallback: string): string => {
  const value = import.meta.env[key] as string | undefined;
  if (value === undefined || value === '') {
    if (import.meta.env.DEV) {
      return fallback;
    }
    console.warn(`Environment variable ${key} is not set. Using fallback: ${fallback}`);
    return fallback;
  }
  return value;
};

const getEnvBoolean = (key: string, fallback: boolean): boolean => {
  const value = import.meta.env[key] as string | undefined;
  if (value === undefined || value === '') {
    return fallback;
  }
  return value === 'true' || value === '1';
};

const getEnvNumber = (key: string, fallback: number): number => {
  const value = import.meta.env[key] as string | undefined;
  if (value === undefined || value === '') {
    return fallback;
  }
  const parsed = Number(value);
  if (isNaN(parsed)) {
    console.warn(`Environment variable ${key} is not a valid number. Using fallback: ${fallback}`);
    return fallback;
  }
  return parsed;
};

const validateApiUrl = (url: string): string => {
  try {
    new URL(url);
    return url;
  } catch {
    throw new Error(`Invalid API_BASE_URL: ${url}. Must be a valid URL.`);
  }
};

const config: AppConfig = {
  apiBaseUrl: validateApiUrl(
    getEnvVariable('VITE_API_BASE_URL', 'http://localhost:8000')
  ),
  apiVersion: getEnvVariable('VITE_API_VERSION', 'v1'),
  appVersion: getEnvVariable('VITE_APP_VERSION', '1.0.0'),
  environment: (getEnvVariable('VITE_ENVIRONMENT', 'development') as 'development' | 'production' | 'staging'),
  buildTimestamp: getEnvVariable('VITE_BUILD_TIMESTAMP', new Date().toISOString()),
};

const featureFlags: FeatureFlags = {
  enableRealtimeUpdates: getEnvBoolean('VITE_ENABLE_REALTIME_UPDATES', false),
  enableBatchUpload: getEnvBoolean('VITE_ENABLE_BATCH_UPLOAD', true),
  enableQRDownload: getEnvBoolean('VITE_ENABLE_QR_DOWNLOAD', true),
  enableKPIPolling: getEnvBoolean('VITE_ENABLE_KPI_POLLING', true),
  kpiRefreshIntervalMs: getEnvNumber('VITE_KPI_REFRESH_INTERVAL_MS', 1000),
};

export const getApiBaseUrl = (): string => config.apiBaseUrl;

export const getFullApiUrl = (endpoint: string): string => {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const cleanBaseUrl = config.apiBaseUrl.endsWith('/')
    ? config.apiBaseUrl.slice(0, -1)
    : config.apiBaseUrl;
  const versionPrefix = config.apiVersion.startsWith('/')
    ? config.apiVersion
    : `/${config.apiVersion}`;
  return `${cleanBaseUrl}${versionPrefix}${cleanEndpoint}`;
};

export const isDevelopment = (): boolean => config.environment === 'development';
export const isProduction = (): boolean => config.environment === 'production';
export const isStaging = (): boolean => config.environment === 'staging';

export const isFeatureEnabled = (flag: keyof FeatureFlags): boolean => {
  return featureFlags[flag] as boolean;
};

export { config, featureFlags };
export default config;
