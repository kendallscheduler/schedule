// Use same-origin; Next.js rewrites /api/* to backend (avoids CORS)
const API = '';
const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchApi<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: { 'Content-Type': 'application/json', ...opts?.headers },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  years: () => fetchApi<{ id: number; name: string; start_date?: string }[]>('/api/years/'),
  getYear: (yearId: number) => fetchApi<{ id: number; name: string; start_date?: string }>(`/api/years/${yearId}`),
  createYear: (name: string, startDate?: string) =>
    fetchApi<{ id: number; name: string }>('/api/years/', {
      method: 'POST',
      body: JSON.stringify({ name, start_date: startDate || '' }),
    }),
  deleteYear: (yearId: number) =>
    fetchApi<{ ok: boolean; deleted: string }>(`/api/years/${yearId}`, { method: 'DELETE' }),
  residents: (yearId?: number) =>
    fetchApi<any[]>(yearId != null ? `/api/residents?year_id=${yearId}` : '/api/residents'),
  cohorts: (yearId: number) => fetchApi<{ id: number; name: string }[]>(`/api/cohorts?year_id=${yearId}`),
  createResident: (data: { name: string; pgy: string; year_id: number; cohort_id?: number; track?: string }) =>
    fetchApi<any>('/api/residents/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateResident: (residentId: number, data: { name?: string; pgy?: string; cohort_id?: number; track?: string }) =>
    fetchApi<any>(`/api/residents/${residentId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  pasteSchedule: (residentId: number, yearId: number, assignments: string) =>
    fetchApi<{ ok: boolean; assignments_added: number }>(`/api/residents/${residentId}/schedule-assignments`, {
      method: 'POST',
      body: JSON.stringify({ year_id: yearId, assignments }),
    }),
  requirements: () => fetchApi<any[]>('/api/requirements/'),
  syncRequirements: () =>
    fetchApi<{ ok: boolean; total_requirements: number }>('/api/requirements/sync', { method: 'POST' }),
  updateRequirement: (reqId: number, data: { required_weeks: number }) =>
    fetchApi<any>(`/api/requirements/${reqId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  vacations: (yearId?: number) =>
    fetchApi<any[]>(yearId != null ? `/api/vacations?year_id=${yearId}` : '/api/vacations'),
  getResidentVacationRequests: (residentId: number, yearId: number) =>
    fetchApi<{ block_a_option1_start: number | null; block_a_option2_start: number | null; block_b_option1_start: number | null; block_b_option2_start: number | null }>(
      `/api/vacations/resident/${residentId}?year_id=${yearId}`
    ),
  upsertResidentVacationRequests: (data: { resident_id: number; year_id: number; block_a_option1_start?: number; block_a_option2_start?: number; block_b_option1_start?: number; block_b_option2_start?: number }) =>
    fetchApi<{ ok: boolean; created: number }>('/api/vacations/resident/upsert', { method: 'POST', body: JSON.stringify(data) }),
  completions: (residentId: number) =>
    fetchApi<{ id: number; resident_id: number; category: string; completed_weeks: number }[]>(
      `/api/completions/resident/${residentId}`
    ),
  rotationHistory: (residentId: number) =>
    fetchApi<{ history: { year_name: string; pgy: string; assignments: { week: number; rotation: string }[]; by_category?: Record<string, number> }[] }>(
      `/api/residents/${residentId}/rotation-history`
    ),
  upsertCompletion: (data: { resident_id: number; category: string; completed_weeks: number; source?: string; year_id?: number }) =>
    fetchApi<any>('/api/completions/', {
      method: 'POST',
      body: JSON.stringify({ ...data, source: data.source ?? 'manual' }),
    }),
  scheduleAssignments: (yearId: number) =>
    fetchApi<Record<number, Record<number, string>>>(`/api/schedule/assignments?year_id=${yearId}`),
  updateAssignment: (data: { resident_id: number; year_id: number; week_number: number; rotation_code: string }) =>
    fetchApi<{ ok: boolean }>('/api/schedule/assignment', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  remaining: (yearId: number) =>
    fetchApi<{ resident_id: number; resident_name: string; pgy: string; category: string; required: number; completed: number; remaining: number }[]>(
      `/api/schedule/remaining?year_id=${yearId}`
    ),
  generate: (yearId: number, timeLimit = 0) =>
    fetch(`${BACKEND}/api/schedule/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ year_id: yearId, time_limit_seconds: timeLimit }),
    }).then(async (res) => {
      const text = await res.text();
      if (!res.ok) throw new Error(text || res.statusText);
      return JSON.parse(text) as { success: boolean; status: string; message?: string; conflicts: string[] };
    }),
  clearSchedule: (yearId: number, residentId?: number, confirmText = '') =>
    fetchApi<{ ok: boolean; cleared: number; backup_id: number }>('/api/schedule/clear', {
      method: 'POST',
      body: JSON.stringify({ year_id: yearId, resident_id: residentId ?? null, confirm_text: confirmText }),
    }),
  scheduleBackups: (yearId: number) =>
    fetchApi<{ id: number; year_id: number; description: string; created_at: string }[]>(
      `/api/schedule/backups?year_id=${yearId}`
    ),
  restoreBackup: (backupId: number) =>
    fetchApi<{ ok: boolean; restored: number }>(`/api/schedule/restore/${backupId}`, { method: 'POST' }),
};
