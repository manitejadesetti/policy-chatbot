import { useRef, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const ACCEPTED = '.txt,.md,.csv,.pdf'

function FileIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  )
}

export default function DocumentUpload() {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [uploads, setUploads] = useState([]) // { name, status, detail }

  function addEntry(name) {
    const id = crypto.randomUUID()
    setUploads((prev) => [...prev, { id, name, status: 'uploading', detail: '' }])
    return id
  }

  function updateEntry(id, patch) {
    setUploads((prev) => prev.map((u) => (u.id === id ? { ...u, ...patch } : u)))
  }

  async function uploadFile(file) {
    const id = addEntry(file.name)
    const form = new FormData()
    form.append('file', file)

    try {
      const res = await fetch(`${API_BASE}/api/documents/upload`, { method: 'POST', body: form })
      const data = await res.json()
      if (!res.ok) {
        updateEntry(id, { status: 'error', detail: data.detail ?? 'Upload failed.' })
      } else {
        updateEntry(id, {
          status: 'done',
          detail: `${data.chunk_count} chunk${data.chunk_count !== 1 ? 's' : ''} embedded`,
        })
      }
    } catch {
      updateEntry(id, { status: 'error', detail: 'Network error.' })
    }
  }

  function handleFiles(files) {
    for (const file of files) uploadFile(file)
  }

  function onInputChange(e) {
    handleFiles(Array.from(e.target.files ?? []))
    e.target.value = ''
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    handleFiles(Array.from(e.dataTransfer.files))
  }

  return (
    <section id="upload">
      <h2>Upload Documents</h2>
      <p className="upload-hint">
        Upload policy documents (PDF, TXT, MD, CSV) to build the knowledge base.
      </p>

      {/* Drop zone */}
      <div
        className={`drop-zone${dragging ? ' dragging' : ''}`}
        role="button"
        tabIndex={0}
        aria-label="Upload document"
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <FileIcon />
        <span>Drag &amp; drop files here, or <strong>click to browse</strong></span>
        <span className="drop-zone-types">PDF · TXT · MD · CSV — up to 10 MB</span>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED}
          multiple
          hidden
          onChange={onInputChange}
        />
      </div>

      {/* Upload list */}
      {uploads.length > 0 && (
        <ul className="upload-list" aria-label="Uploaded documents">
          {uploads.map((u) => (
            <li key={u.id} className={`upload-item ${u.status}`}>
              <span className="upload-name" title={u.name}>{u.name}</span>
              <span className="upload-status">
                {u.status === 'uploading' && <span className="upload-spinner" aria-label="Uploading" />}
                {u.status === 'done' && '✓ '}
                {u.detail || (u.status === 'uploading' ? 'Uploading…' : '')}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
