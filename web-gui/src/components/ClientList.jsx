import React from 'react'
import { Monitor, Terminal, Play, Square, Wifi, WifiOff } from 'lucide-react'

const ClientList = ({ clients, selectedClient, onSelectClient, onStartTerminal, onStartScreenShare, onStopScreenShare }) => {
  return (
    <div className="client-list">
      {Object.entries(clients).length === 0 ? (
        <p className="text-muted">No machines connected</p>
      ) : (
        Object.entries(clients).map(([id, client]) => (
          <div
            key={id}
            className={`client-item ${selectedClient === id ? 'selected' : ''}`}
            onClick={() => onSelectClient(id)}
          >
            <div className="client-header">
              <div className="client-info">
                <div className="client-name">
                  {client.system_info?.hostname || id.substring(0, 8)}
                </div>
                <div className="client-os">
                  {client.system_info?.os || 'Unknown'}
                </div>
              </div>
              <div className={`client-status ${client.status}`}>
                {client.status === 'online' ? <Wifi size={14} /> : <WifiOff size={14} />}
              </div>
            </div>
            
            {client.system_info && (
              <div className="client-stats">
                <span className="stat">CPU: {client.system_info.cpu_percent}%</span>
                <span className="stat">RAM: {client.system_info.memory_percent}%</span>
              </div>
            )}
            
            <div className="client-actions">
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onStartTerminal(id)
                }}
                className="action-btn"
                title="Open Terminal"
              >
                <Terminal size={16} />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onStartScreenShare(id)
                }}
                className="action-btn"
                title="Start Screen Share"
              >
                <Play size={16} />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onStopScreenShare(id)
                }}
                className="action-btn"
                title="Stop Screen Share"
              >
                <Square size={16} />
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  )
}

export default ClientList
