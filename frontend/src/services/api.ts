import { apiFetch, apiUploadFile } from '../lib/api';
import type {
  ReturnRequest,
  ReturnRequestCreate,
  ReturnsFilters,
  PaginatedResponse,
  DecisionResult,
  DecisionInput,
  BatchUploadResponse,
  KPIMetrics,
  DestinationDistribution,
  Alert,
  AlertFilters,
  DropOffPoint,
  NearestDropOffPointsRequest,
  PickupSlot,
  PickupScheduleRequest,
  PickupScheduleResponse,
  KAMApprovalRequest,
  KAMApprovalResponse,
  TrackingTimeline,
  ReportRequest,
} from '../types/models';

export const returnsApi = {
  list: async (filters?: ReturnsFilters): Promise<PaginatedResponse<ReturnRequest>> => {
    const params = new URLSearchParams();
    if (filters?.page) params.set('page', String(filters.page));
    if (filters?.page_size) params.set('page_size', String(filters.page_size));
    if (filters?.channel) params.set('channel', filters.channel);
    if (filters?.status) params.set('status', filters.status);
    if (filters?.destination) params.set('destination', filters.destination);
    if (filters?.customer_id) params.set('customer_id', filters.customer_id);
    if (filters?.date_from) params.set('date_from', filters.date_from);
    if (filters?.date_to) params.set('date_to', filters.date_to);
    if (filters?.sort_by) params.set('sort_by', filters.sort_by);
    if (filters?.sort_order) params.set('sort_order', filters.sort_order);

    const queryString = params.toString();
    const path = `/api/v1/returns${queryString ? `?${queryString}` : ''}`;
    return apiFetch<PaginatedResponse<ReturnRequest>>(path);
  },

  getById: async (returnId: string): Promise<ReturnRequest> => {
    return apiFetch<ReturnRequest>(`/api/v1/returns/${returnId}`);
  },

  create: async (data: ReturnRequestCreate): Promise<ReturnRequest> => {
    return apiFetch<ReturnRequest>('/api/v1/returns', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: async (returnId: string, data: Partial<ReturnRequest>): Promise<ReturnRequest> => {
    return apiFetch<ReturnRequest>(`/api/v1/returns/${returnId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  evaluate: async (input: DecisionInput): Promise<DecisionResult> => {
    return apiFetch<DecisionResult>('/api/v1/returns/evaluate', {
      method: 'POST',
      body: JSON.stringify(input),
    });
  },

  getTracking: async (returnId: string): Promise<TrackingTimeline> => {
    return apiFetch<TrackingTimeline>(`/api/v1/returns/${returnId}/tracking`);
  },
};

export const batchesApi = {
  upload: async (
    file: File,
    customerId: string,
    returnReason: string,
    kamApprovalReference?: string
  ): Promise<BatchUploadResponse> => {
    const additionalFields: Record<string, string> = {
      customer_id: customerId,
      return_reason: returnReason,
    };
    if (kamApprovalReference) {
      additionalFields.kam_approval_reference = kamApprovalReference;
    }
    return apiUploadFile<BatchUploadResponse>('/api/v1/batches/upload', file, additionalFields);
  },
};

export const controlTowerApi = {
  getKPIs: async (): Promise<KPIMetrics> => {
    return apiFetch<KPIMetrics>('/api/v1/control-tower/kpis');
  },

  getDistribution: async (): Promise<DestinationDistribution> => {
    return apiFetch<DestinationDistribution>('/api/v1/control-tower/distribution');
  },

  getAlerts: async (filters?: AlertFilters): Promise<Alert[]> => {
    const params = new URLSearchParams();
    if (filters?.priority) params.set('priority', filters.priority);
    if (filters?.acknowledged !== undefined) params.set('acknowledged', String(filters.acknowledged));
    if (filters?.limit) params.set('limit', String(filters.limit));

    const queryString = params.toString();
    const path = `/api/v1/control-tower/alerts${queryString ? `?${queryString}` : ''}`;
    return apiFetch<Alert[]>(path);
  },

  acknowledgeAlert: async (alertId: string): Promise<Alert> => {
    return apiFetch<Alert>(`/api/v1/control-tower/alerts/${alertId}/acknowledge`, {
      method: 'POST',
    });
  },
};

export const dropoffApi = {
  getNearest: async (request: NearestDropOffPointsRequest): Promise<DropOffPoint[]> => {
    const params = new URLSearchParams();
    if (request.latitude !== undefined) params.set('latitude', String(request.latitude));
    if (request.longitude !== undefined) params.set('longitude', String(request.longitude));
    if (request.max_distance_km) params.set('max_distance_km', String(request.max_distance_km));

    const queryString = params.toString();
    const path = `/api/v1/dropoff/points${queryString ? `?${queryString}` : ''}`;
    return apiFetch<DropOffPoint[]>(path);
  },

  getById: async (pointId: string): Promise<DropOffPoint> => {
    return apiFetch<DropOffPoint>(`/api/v1/dropoff/points/${pointId}`);
  },
};

export const pickupApi = {
  getSlots: async (returnId: string): Promise<PickupSlot[]> => {
    return apiFetch<PickupSlot[]>(`/api/v1/pickup/slots?return_id=${returnId}`);
  },

  schedule: async (request: PickupScheduleRequest): Promise<PickupScheduleResponse> => {
    return apiFetch<PickupScheduleResponse>('/api/v1/pickup/schedule', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },
};

export const kamApi = {
  getPending: async (): Promise<ReturnRequest[]> => {
    return apiFetch<ReturnRequest[]>('/api/v1/kam/pending-approvals');
  },

  approve: async (returnId: string, request?: KAMApprovalRequest): Promise<KAMApprovalResponse> => {
    return apiFetch<KAMApprovalResponse>(`/api/v1/kam/approve/${returnId}`, {
      method: 'POST',
      body: JSON.stringify(request || {}),
    });
  },

  reject: async (returnId: string, reason: string): Promise<ReturnRequest> => {
    return apiFetch<ReturnRequest>(`/api/v1/kam/reject/${returnId}`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },
};

export const reportsApi = {
  generate: async (request: ReportRequest): Promise<{ report_id: string; download_url: string }> => {
    return apiFetch<{ report_id: string; download_url: string }>('/api/v1/reports/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  download: async (reportId: string): Promise<Blob> => {
    const response = await fetch(`/api/v1/reports/${reportId}/download`);
    if (!response.ok) {
      throw new Error('Failed to download report');
    }
    return response.blob();
  },
};
