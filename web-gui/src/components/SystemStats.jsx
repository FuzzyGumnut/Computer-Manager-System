import React from 'react'
import { Cpu, HardDrive, Activity } from 'lucide-react'

const SystemStats = ({ client }) => {
  const info = client?.system_info

  if (!info) {
    return (
      <div className="system-stats">
        <p className="text-muted">No system information available</p>
      </div>
    )
  }

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="system-stats">
      <h3>System Statistics</h3>
      
      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-icon">
            <Cpu size={24} />
          </div>
          <div className="stat-content">
            <h4>CPU</h4>
            <div className="stat-value">{info.cpu_percent}%</div>
            <div className="stat-detail">{info.cpu_count} cores</div>
          </div>
        </div>

        <div className="stat-item">
          <div className="stat-icon">
            <Activity size={24} />
          </div>
          <div className="stat-content">
            <h4>Memory</h4>
            <div className="stat-value">{info.memory_percent}%</div>
            <div className="stat-detail">
              {formatBytes(info.memory_available)} / {formatBytes(info.memory_total)}
            </div>
          </div>
        </div>

        <div className="stat-item">
          <div className="stat-icon">
            <HardDrive size={24} />
          </div>
          <div className="stat-content">
            <h4>Storage</h4>
            <div className="stat-value">{info.disk_percent}%</div>
            <div className="stat-detail">
              {formatBytes(info.disk_used)} / {formatBytes(info.disk_total)}
            </div>
          </div>
        </div>
      </div>

      <div className="system-info">
        <h4>System Information</h4>
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Hostname:</span>
            <span className="info-value">{info.hostname}</span>
          </div>
          <div className="info-item">
            <span className="info-label">OS:</span>
            <span className="info-value">{info.os}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Version:</span>
            <span className="info-value">{info.os_version}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Architecture:</span>
            <span className="info-value">{info.architecture}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SystemStats
