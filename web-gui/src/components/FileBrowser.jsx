import React, { useState, useEffect } from 'react'
import { Folder, File, ArrowLeft, Home, Search, Download, Trash2 } from 'lucide-react'

const FileBrowser = ({ clientId, files, currentPath, onListDirectory }) => {
  const [localPath, setLocalPath] = useState(currentPath || '.')
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    setLocalPath(currentPath || '.')
  }, [currentPath])

  const handleFileClick = (file) => {
    if (file.is_dir) {
      onListDirectory(clientId, file.path)
    }
  }

  const handleNavigateUp = () => {
    if (localPath !== '.') {
      const parentPath = localPath.split('/').slice(0, -1).join('/') || '.'
      onListDirectory(clientId, parentPath)
    }
  }

  const handleNavigateHome = () => {
    onListDirectory(clientId, '.')
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const filteredFiles = files.filter(file =>
    file.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const sortedFiles = [...filteredFiles].sort((a, b) => {
    if (a.is_dir && !b.is_dir) return -1
    if (!a.is_dir && b.is_dir) return 1
    return a.name.localeCompare(b.name)
  })

  return (
    <div className="file-browser">
      <div className="file-browser-header">
        <div className="file-browser-nav">
          <button onClick={handleNavigateHome} className="nav-btn" title="Home">
            <Home size={18} />
          </button>
          <button onClick={handleNavigateUp} className="nav-btn" title="Up">
            <ArrowLeft size={18} />
          </button>
          <div className="current-path">{currentPath}</div>
        </div>
        <div className="file-browser-search">
          <Search size={16} />
          <input
            type="text"
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="file-list">
        {sortedFiles.length === 0 ? (
          <div className="empty-state">
            <Folder size={48} />
            <p>No files found</p>
          </div>
        ) : (
          sortedFiles.map((file, index) => (
            <div
              key={index}
              className={`file-item ${file.is_dir ? 'directory' : 'file'}`}
              onClick={() => handleFileClick(file)}
            >
              <div className="file-icon">
                {file.is_dir ? <Folder size={20} /> : <File size={20} />}
              </div>
              <div className="file-info">
                <div className="file-name">{file.name}</div>
                <div className="file-meta">
                  {file.is_dir ? 'Directory' : formatFileSize(file.size)}
                </div>
              </div>
              {!file.is_dir && (
                <div className="file-actions">
                  <button className="action-btn" title="Download">
                    <Download size={16} />
                  </button>
                  <button className="action-btn danger" title="Delete">
                    <Trash2 size={16} />
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default FileBrowser
