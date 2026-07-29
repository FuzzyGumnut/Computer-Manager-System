import React, { useState, useEffect } from 'react'
import { Monitor, Maximize2, Minimize2 } from 'lucide-react'

const ScreenMonitor = ({ clientId }) => {
  const [screenImage, setScreenImage] = useState(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isSharing, setIsSharing] = useState(false)

  useEffect(() => {
    // In a real implementation, this would connect to WebSocket
    // and receive screen updates
    const mockScreenUpdate = () => {
      if (isSharing) {
        // Mock screen capture - in real implementation this comes from WebSocket
        console.log('Screen update for:', clientId)
      }
    }

    const interval = setInterval(mockScreenUpdate, 2000)

    return () => clearInterval(interval)
  }, [clientId, isSharing])

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }

  return (
    <div className={`screen-monitor ${isFullscreen ? 'fullscreen' : ''}`}>
      <div className="screen-header">
        <div className="screen-title">
          <Monitor size={20} />
          <span>Screen Share</span>
        </div>
        <button
          onClick={toggleFullscreen}
          className="icon-btn"
          title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
        >
          {isFullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
        </button>
      </div>
      <div className="screen-content">
        {screenImage ? (
          <img src={`data:image/png;base64,${screenImage}`} alt="Screen" />
        ) : (
          <div className="screen-placeholder">
            <Monitor size={48} />
            <p>Screen sharing not active</p>
            <p className="text-muted">Click "Start Screen Share" to begin</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ScreenMonitor
