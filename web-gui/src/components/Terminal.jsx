import React, { useEffect, useRef, useState } from 'react'
import { Terminal as XTerm } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'

const TerminalComponent = ({ clientId, output, onInput }) => {
  const terminalRef = useRef(null)
  const xtermRef = useRef(null)
  const fitAddonRef = useRef(null)

  useEffect(() => {
    if (terminalRef.current) {
      console.log('Initializing terminal...')
      
      // Create xterm instance
      const xterm = new XTerm({
        theme: {
          background: 'rgba(15, 15, 35, 0.8)',
          foreground: '#ffffff',
          cursor: '#60a5fa',
          cursorAccent: '#ffffff',
          selection: 'rgba(96, 165, 250, 0.3)',
        },
        fontFamily: 'Menlo, Monaco, "Courier New", monospace',
        fontSize: 14,
        lineHeight: 1.2,
        cursorBlink: true,
        cursorStyle: 'block',
        allowProposedApi: true,
      })

      // Create fit addon
      const fitAddon = new FitAddon()
      xterm.loadAddon(fitAddon)

      // Mount to DOM
      xterm.open(terminalRef.current)
      fitAddon.fit()

      // Handle user input with both methods
      xterm.onData((data) => {
        console.log('Terminal data received:', data)
        onInput(data)
      })

      xterm.onKey(({ key, domEvent }) => {
        console.log('Key pressed:', key, 'Event:', domEvent)
        // Don't write here, let onData handle it
      })

      // Store references
      xtermRef.current = xterm
      fitAddonRef.current = fitAddon

      // Welcome message
      xterm.write('\r\n\x1b[1;34mComputer Manager Terminal\x1b[0m\r\n')
      xterm.write('Connected to: ' + clientId + '\r\n\r\n')
      xterm.write('\x1b[32m$\x1b[0m ')

      // Handle resize
      const handleResize = () => {
        fitAddon.fit()
      }
      window.addEventListener('resize', handleResize)

      // Focus terminal on mount
      setTimeout(() => {
        xterm.focus()
      }, 100)

      return () => {
        window.removeEventListener('resize', handleResize)
        xterm.dispose()
      }
    }
  }, [clientId, onInput])

  // Write output when it changes
  useEffect(() => {
    if (xtermRef.current && output) {
      xtermRef.current.write(output)
    }
  }, [output])

  const writeOutput = (output) => {
    if (xtermRef.current) {
      xtermRef.current.write(output)
    }
  }

  const handleFocus = () => {
    if (xtermRef.current) {
      xtermRef.current.focus()
    }
  }

  return (
    <div className="terminal-container" onClick={handleFocus}>
      <div ref={terminalRef} className="terminal" />
    </div>
  )
}

export default TerminalComponent
