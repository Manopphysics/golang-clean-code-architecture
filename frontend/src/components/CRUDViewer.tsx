import { useEffect, useState } from 'react'
import { apiDescribe, apiGetOne, apiList, type AvroSchema, type DataListResponse } from '../api'

const SLUGS = ['users', 'user-tokens', 'user-permissions']

const s = {
  card: { background: '#1e293b', borderRadius: 12, padding: '1.5rem', border: '1px solid #334155' },
  header: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap' as const, gap: '0.75rem' },
  cardTitle: { fontSize: '.7rem', textTransform: 'uppercase' as const, letterSpacing: '.1em', color: '#64748b', fontWeight: 600 },
  controls: { display: 'flex', gap: '0.625rem', flexWrap: 'wrap' as const, alignItems: 'center' },
  select: { padding: '0.4rem 0.75rem', background: '#0f172a', border: '1px solid #475569', borderRadius: 6, color: '#e2e8f0', fontSize: '.85rem', cursor: 'pointer' },
  schemaBtn: (active: boolean): React.CSSProperties => ({
    padding: '0.375rem 0.75rem', borderRadius: 6, cursor: 'pointer', fontSize: '.8rem', fontWeight: 500, border: '1px solid #475569',
    background: active ? '#334155' : 'transparent', color: active ? '#f1f5f9' : '#64748b',
  }),
  table: { width: '100%', borderCollapse: 'collapse' as const, fontSize: '.8rem' },
  th: { textAlign: 'left' as const, padding: '0.5rem 0.75rem', color: '#64748b', fontWeight: 600, borderBottom: '1px solid #334155', whiteSpace: 'nowrap' as const, fontSize: '.72rem', textTransform: 'uppercase' as const, letterSpacing: '.05em' },
  td: { padding: '0.5rem 0.75rem', borderBottom: '1px solid #1e293b', color: '#cbd5e1', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const },
  trHover: { cursor: 'pointer' },
  empty: { textAlign: 'center' as const, color: '#475569', padding: '2rem', fontSize: '.875rem' },
  pagination: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '1rem' },
  pageInfo: { color: '#64748b', fontSize: '.8rem' },
  pageBtn: (disabled: boolean): React.CSSProperties => ({
    padding: '0.375rem 0.75rem', border: '1px solid #334155', borderRadius: 6, background: 'transparent',
    color: disabled ? '#334155' : '#94a3b8', cursor: disabled ? 'default' : 'pointer', fontSize: '.8rem',
  }),
  schemaBox: { background: '#0f172a', borderRadius: 8, padding: '1rem', marginTop: '1rem' },
  schemaTitle: { color: '#6366f1', fontSize: '.8rem', fontWeight: 700, marginBottom: '0.5rem' },
  schemaField: { display: 'flex', justifyContent: 'space-between', padding: '0.3rem 0', borderBottom: '1px solid #1e293b', fontSize: '.8rem' },
  fieldName: { color: '#e2e8f0' },
  fieldType: { color: '#6366f1', fontFamily: 'monospace' },
  detail: { background: '#0f172a', borderRadius: 8, padding: '1rem', marginTop: '1rem' },
  detailTitle: { color: '#94a3b8', fontSize: '.75rem', fontWeight: 600, marginBottom: '0.5rem' },
  pre: { color: '#86efac', fontSize: '.78rem', fontFamily: 'monospace', whiteSpace: 'pre-wrap' as const, wordBreak: 'break-all' as const },
  loading: { color: '#64748b', fontSize: '.875rem', textAlign: 'center' as const, padding: '1.5rem' },
  err: { color: '#fca5a5', fontSize: '.8rem', background: '#450a0a', border: '1px solid #dc2626', borderRadius: 6, padding: '0.5rem 0.75rem', marginTop: '0.5rem' },
} as const

export default function CRUDViewer() {
  const [slug, setSlug] = useState(SLUGS[0])
  const [data, setData] = useState<DataListResponse | null>(null)
  const [schema, setSchema] = useState<AvroSchema | null>(null)
  const [showSchema, setShowSchema] = useState(false)
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const loadData = async (s: string, p: number) => {
    setLoading(true); setError(''); setDetail(null)
    try {
      const [list, sch] = await Promise.all([apiList(s, p, 10), apiDescribe(s)])
      setData(list); setSchema(sch)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load')
    } finally { setLoading(false) }
  }

  useEffect(() => { loadData(slug, 1); setPage(1) }, [slug])

  const handleRowClick = async (row: Record<string, unknown>) => {
    if (!row.id) return
    try {
      const res = await apiGetOne(slug, String(row.id))
      setDetail(res.data)
    } catch { /* ignore */ }
  }

  const columns = schema?.fields.map(f => f.name) ?? []

  return (
    <div style={s.card}>
      <div style={s.header}>
        <p style={s.cardTitle}>Data Explorer</p>
        <div style={s.controls}>
          <select style={s.select} value={slug} onChange={e => setSlug(e.target.value)}>
            {SLUGS.map(sl => <option key={sl} value={sl}>{sl}</option>)}
          </select>
          <button style={s.schemaBtn(showSchema)} onClick={() => setShowSchema(v => !v)}>
            {showSchema ? 'Hide Schema' : 'Schema'}
          </button>
        </div>
      </div>

      {error && <div style={s.err}>{error}</div>}

      {showSchema && schema && (
        <div style={s.schemaBox}>
          <p style={s.schemaTitle}>{schema.name} — {schema.type}</p>
          {schema.fields.map(f => (
            <div key={f.name} style={s.schemaField}>
              <span style={s.fieldName}>{f.name}</span>
              <span style={s.fieldType}>{f.type}</span>
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <p style={s.loading}>Loading…</p>
      ) : (
        <>
          <div style={{ overflowX: 'auto' }}>
            <table style={s.table}>
              <thead>
                <tr>{columns.map(c => <th key={c} style={s.th}>{c}</th>)}</tr>
              </thead>
              <tbody>
                {data?.data.length === 0 ? (
                  <tr><td colSpan={columns.length} style={s.empty}>No records found</td></tr>
                ) : (
                  data?.data.map((row, i) => (
                    <tr key={i} style={s.trHover} onClick={() => handleRowClick(row)}>
                      {columns.map(c => (
                        <td key={c} style={s.td} title={String(row[c] ?? '')}>
                          {String(row[c] ?? '—')}
                        </td>
                      ))}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {data && (
            <div style={s.pagination}>
              <span style={s.pageInfo}>
                {data.total_data} record{data.total_data !== 1 ? 's' : ''} · page {data.page} of {data.total_page}
              </span>
              <div style={{ display: 'flex', gap: 6 }}>
                <button style={s.pageBtn(page <= 1)} disabled={page <= 1} onClick={() => { const p = page - 1; setPage(p); loadData(slug, p) }}>← Prev</button>
                <button style={s.pageBtn(page >= data.total_page)} disabled={page >= data.total_page} onClick={() => { const p = page + 1; setPage(p); loadData(slug, p) }}>Next →</button>
              </div>
            </div>
          )}
        </>
      )}

      {detail && (
        <div style={s.detail}>
          <p style={s.detailTitle}>Record Detail</p>
          <pre style={s.pre}>{JSON.stringify(detail, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
