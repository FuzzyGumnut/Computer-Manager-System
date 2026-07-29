import React, { useState, useEffect, useRef } from 'react'
import { Monitor, Terminal, Cpu, HardDrive, Wifi, Power, Play, Square, Command, Folder } from 'lucide-react'
import TerminalComponent from './components/Terminal'
import ScreenMonitor from './components/ScreenMonitor'
import SystemStats from './components/SystemStats'
import ClientList from './components/ClientList'
import FileBrowser from './components/FileBrowser'

function App() {
  const [clients, setClients] = useState({})
  const [selectedClient, setSelectedClient] = useState(null)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [connected, setConnected] = useState(false)
  const [terminalOutput, setTerminalOutput] = useState('')
  const [directoryFiles, setDirectoryFiles] = useState([])
  const [currentPath, setCurrentPath] = useState('.')
  const wsRef = useRef(null)

  useEffect(() => {
    // Connect to WebSocket server
    const ws = new WebSocket('ws://localhost:8765')
    
    ws.onopen = () => {
      console.log('Connected to server')
      setConnected(true)
      // Request clients list
      ws.send(JSON.stringify({ type: 'get_clients' }))
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'clients_list') {
        setClients(data.clients)
      } else if (data.type === 'screen_update') {
        // Handle screen updates
        console.log('Screen update received')
      } else if (data.type === 'terminal_output') {
        // Handle terminal output
        console.log('Terminal output received:', data.output)
        setTerminalOutput(prev => prev + data.output)
      } else if (data.type === 'command_result') {
        // Handle command results
        console.log('Command result:', data.result)
      } else if (data.type === 'directory_list') {
        // Handle directory listing
        console.log('Directory list received:', data.files)
        if (data.client_id === selectedClient) {
          setDirectoryFiles(data.files)
          setCurrentPath(data.path)
        }
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setConnected(false)
    }
    
    ws.onclose = () => {
      console.log('Disconnected from server')
      setConnected(false)
    }
    
    wsRef.current = ws
    
    return () => {
      ws.close()
    }
  }, [])

  const sendMessage = (message) => {
    console.log('Sending message:', message)
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.error('WebSocket not connected, readyState:', wsRef.current?.readyState)
    }
  }

  const handleSelectClient = (clientId) => {
    setSelectedClient(clientId)
    setActiveTab('monitor')
  }

  const handleStartTerminal = (clientId) => {
    console.log('Starting terminal for:', clientId)
    sendMessage({
      type: 'start_terminal',
      client_id: clientId
    })
    setSelectedClient(clientId)
    setActiveTab('terminal')
  }

  const handleStartScreenShare = (clientId) => {
    console.log('Starting screen share for:', clientId)
    sendMessage({
      type: 'start_screen_share',
      client_id: clientId
    })
  }

  const handleStopScreenShare = (clientId) => {
    console.log('Stopping screen share for:', clientId)
    sendMessage({
      type: 'stop_screen_share',
      client_id: clientId
    })
  }

  const handleSendCommand = (clientId, command) => {
    sendMessage({
      type: 'send_command',
      client_id: clientId,
      command: command
    })
  }

  const handleTerminalInput = (clientId, input) => {
    console.log('Terminal input:', input)
    sendMessage({
      type: 'terminal_input',
      client_id: clientId,
      input: input
    })
  }

  const handleListDirectory = (clientId, path) => {
    sendMessage({
      type: 'list_directory',
      client_id: clientId,
      path: path
    })
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <Monitor className="logo-icon" size={32} />
          <h1>Computer Manager</h1>
        </div>
        <div className="header-right">
          <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
            <Wifi size={16} />
            <span>{connected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="main-content">
        {/* Sidebar */}
        <aside className="sidebar">
          <nav className="nav">
            <button
              className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveTab('dashboard')}
            >
              <Monitor size={20} />
              <span>Dashboard</span>
            </button>
            <button
              className={`nav-item ${activeTab === 'monitor' ? 'active' : ''}`}
              onClick={() => setActiveTab('monitor')}
              disabled={!selectedClient}
            >
              <Cpu size={20} />
              <span>Monitor</span>
            </button>
            <button
              className={`nav-item ${activeTab === 'terminal' ? 'active' : ''}`}
              onClick={() => setActiveTab('terminal')}
              disabled={!selectedClient}
            >
              <Terminal size={20} />
              <span>Terminal</span>
            </button>
            <button
              className={`nav-item ${activeTab === 'files' ? 'active' : ''}`}
              onClick={() => setActiveTab('files')}
              disabled={!selectedClient}
            >
              <Folder size={20} />
              <span>Files</span>
            </button>
          </nav>

          <div className="clients-section">
            <h3>Connected Machines</h3>
            <ClientList
              clients={clients}
              selectedClient={selectedClient}
              onSelectClient={handleSelectClient}
              onStartTerminal={handleStartTerminal}
              onStartScreenShare={handleStartScreenShare}
              onStopScreenShare={handleStopScreenShare}
            />
          </div>
        </aside>

        {/* Main Panel */}
        <main className="main-panel">
          {activeTab === 'dashboard' && (
            <div className="dashboard">
              <h2>Dashboard</h2>
              <div className="stats-grid">
                <div className="stat-card">
                  <Monitor size={24} />
                  <div>
                    <h3>{Object.keys(clients).length}</h3>
                    <p>Total Machines</p>
                  </div>
                </div>
                <div className="stat-card">
                  <Wifi size={24} />
                  <div>
                    <h3>{Object.values(clients).filter(c => c.status === 'online').length}</h3>
                    <p>Online</p>
                  </div>
                </div>
                <div className="stat-card">
                  <Power size={24} />
                  <div>
                    <h3>{Object.values(clients).filter(c => c.status === 'offline').length}</h3>
                    <p>Offline</p>
                  </div>
                </div>
              </div>

              <div className="recent-activity">
                <h3>System Overview</h3>
                {Object.entries(clients).map(([id, client]) => (
                  <div key={id} className="activity-item">
                    <div className="activity-header">
                      <span className="activity-name">
                        {client.system_info?.hostname || id}
                      </span>
                      <span className={`status-badge ${client.status}`}>
                        {client.status}
                      </span>
                    </div>
                    {client.system_info && (
                      <div className="activity-details">
                        <span>{client.system_info.os}</span>
                        <span>CPU: {client.system_info.cpu_percent}%</span>
                        <span>RAM: {client.system_info.memory_percent}%</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'monitor' && selectedClient && (
            <div className="monitor-view">
              <div className="monitor-header">
                <h2>Monitor: {clients[selectedClient]?.system_info?.hostname || selectedClient}</h2>
                <div className="monitor-actions">
                  <button
                    onClick={() => handleStartScreenShare(selectedClient)}
                    className="btn btn-primary"
                  >
                    <Play size={16} />
                    Start Screen Share
                  </button>
                  <button
                    onClick={() => handleStopScreenShare(selectedClient)}
                    className="btn btn-danger"
                  >
                    <Square size={16} />
                    Stop Screen Share
                  </button>
                </div>
              </div>
              
              <ScreenMonitor clientId={selectedClient} />
              <SystemStats client={clients[selectedClient]} />
            </div>
          )}

          {activeTab === 'terminal' && selectedClient && (
            <div className="terminal-view">
              <div className="terminal-header">
                <h2>Terminal: {clients[selectedClient]?.system_info?.hostname || selectedClient}</h2>
                <button
                  onClick={() => handleStartTerminal(selectedClient)}
                  className="btn btn-primary"
                >
                  <Terminal size={16} />
                  Start Terminal
                </button>
              </div>
              <TerminalComponent
                clientId={selectedClient}
                output={terminalOutput}
                onInput={(input) => handleTerminalInput(selectedClient, input)}
              />
            </div>
          )}

          {activeTab === 'files' && selectedClient && (
            <div className="files-view">
              <div className="files-header">
                <h2>Files: {clients[selectedClient]?.system_info?.hostname || selectedClient}</h2>
              </div>
              <FileBrowser
                clientId={selectedClient}
                files={directoryFiles}
                currentPath={currentPath}
                onListDirectory={handleListDirectory}
              />
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
