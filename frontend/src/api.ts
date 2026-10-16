/**
 * API client — thin wrapper around fetch that targets the FastAPI backend.
 * All calls go through the Vite dev proxy at /api → http://localhost:8000/api.
 */

const BASE = '/api/v1'

export interface UserEntity {
  id: number
  email: string
  first_name: string
  last_name: string
  created_at: string
  updated_at: string
}

export interface TokenEntity {
  access: string
  refresh: string
}

export interface LoginResponse {
  user: UserEntity
  token: TokenEntity
}

export interface DataListResponse {
  code: number
  data: Record<string, unknown>[]
  page: number
  page_size: number
  total_page: number
  total_data: number
  message: string
}

export interface AvroField {
  name: string
  type: string
}

export interface AvroSchema {
  type: string
  name: string
  fields: AvroField[]
}

// ---------------------------------------------------------------------------
// Token storage
// ---------------------------------------------------------------------------
const TOKEN_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'

export const auth = {
  getAccess: () => localStorage.getItem(TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  save: (tokens: TokenEntity) => {
    localStorage.setItem(TOKEN_KEY, tokens.access)
    localStorage.setItem(REFRESH_KEY, tokens.refresh)
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
  isLoggedIn: () => !!localStorage.getItem(TOKEN_KEY),
}

// ---------------------------------------------------------------------------
// HTTP helpers
// ---------------------------------------------------------------------------
async function request<T>(
  path: string,
  options: RequestInit = {},
  withAuth = false,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (withAuth) {
    const token = auth.getAccess()
    if (token) headers['Authorization'] = `Bearer ${token}`
  }
  const res = await fetch(`${BASE}${path}`, { ...options, headers })
  const data = await res.json()
  if (!res.ok) {
    throw new Error(data?.message ?? `HTTP ${res.status}`)
  }
  return data as T
}

// ---------------------------------------------------------------------------
// Auth endpoints
// ---------------------------------------------------------------------------
export const apiRegister = (
  email: string,
  password: string,
  first_name: string,
  last_name: string,
) =>
  request<UserEntity>('/users/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, first_name, last_name }),
  })

export const apiLogin = (email: string, password: string) =>
  request<LoginResponse>('/users/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })

export const apiLogout = (refresh_token: string) =>
  request<null>('/users/logout', {
    method: 'POST',
    body: JSON.stringify({ refresh_token }),
  })

export const apiProfile = () =>
  request<UserEntity>('/users/profile', { method: 'GET' }, true)

// ---------------------------------------------------------------------------
// CRUD endpoints
// ---------------------------------------------------------------------------
export const apiDescribe = (slug: string) =>
  request<AvroSchema>(`/data/${slug}/describe`, { method: 'GET' }, true)

export const apiList = (slug: string, page = 1, pageSize = 10) =>
  request<DataListResponse>(
    `/data/${slug}/?_page=${page}&_pageSize=${pageSize}`,
    { method: 'GET' },
    true,
  )

export const apiGetOne = (slug: string, id: string) =>
  request<{ code: number; data: Record<string, unknown> }>(
    `/data/${slug}/${id}`,
    { method: 'GET' },
    true,
  )
