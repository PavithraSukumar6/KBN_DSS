import React, { useState, useEffect } from 'react';
import { Cloud, Trash2, RefreshCw, FileCheck, Layers, Play, AlertCircle, CheckCircle } from 'lucide-react';

const CloudManager = () => {
    const [isConnected, setIsConnected] = useState(false);
    const [isMock, setIsMock] = useState(false);
    const [files, setFiles] = useState([]);
    const [logs, setLogs] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [account, setAccount] = useState('');

    useEffect(() => {
        checkStatus();
    }, []);

    const checkStatus = async () => {
        try {
            const res = await fetch('http://localhost:5000/cloud/status');
            const data = await res.json();
            setIsConnected(data.connected);
            setIsMock(data.is_mock);
            setAccount(data.email);
            if (data.connected) fetchFiles();
        } catch (error) {
            log("Error connecting to backend.", "error");
        }
    };

    const fetchFiles = async () => {
        try {
            const res = await fetch('http://localhost:5000/cloud/files');
            const data = await res.json();
            setFiles(data);
        } catch (error) {
            log("Failed to fetch file list.", "error");
        }
    };

    const handleLogin = async () => {
        setIsLoading(true);
        try {
            const res = await fetch('http://localhost:5000/cloud/login', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                checkStatus();
                log("Logged in successfully.");
            } else {
                log("Login failed.", "error");
            }
        } catch (error) {
            log("Login error.", "error");
        }
        setIsLoading(false);
    };

    const runAction = async (action, label) => {
        setIsLoading(true);
        log(`Starting ${label}...`);
        try {
            const res = await fetch('http://localhost:5000/cloud/action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action })
            });
            const data = await res.json();

            if (res.ok) {
                log(`${label} Completed.`);
                if (data.details && Array.isArray(data.details)) {
                    data.details.forEach(d => log(`> ${d}`));
                } else if (data.details) {
                    log(`> ${JSON.stringify(data.details)}`);
                }
                fetchFiles();
            } else {
                log(`Error: ${data.error}`, "error");
            }
        } catch (error) {
            log(`Action failed: ${error}`, "error");
        }
        setIsLoading(false);
    };

    const log = (msg, type = 'info') => {
        setLogs(prev => [{ time: new Date().toLocaleTimeString(), msg, type }, ...prev]);
    };

    return (
        <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <div>
                    <h2 style={{ fontSize: '1.8rem', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Cloud size={32} color="#3b82f6" /> Cloud Manager
                    </h2>
                    <p style={{ color: 'var(--text-muted)' }}>Manage remote files directly via API</p>
                </div>

                {isConnected && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <span style={{
                            background: isMock ? '#f59e0b20' : '#10b98120',
                            color: isMock ? '#f59e0b' : '#10b981',
                            padding: '0.5rem 1rem',
                            borderRadius: '20px',
                            fontSize: '0.9rem',
                            border: `1px solid ${isMock ? '#f59e0b' : '#10b981'}`
                        }}>
                            {isMock ? '⚠️ Mock Mode' : '✅ Connected'} ({account})
                        </span>
                        <button onClick={fetchFiles} className="btn" style={{ padding: '0.5rem' }} title="Refresh Files">
                            <RefreshCw size={20} />
                        </button>
                    </div>
                )}
            </div>

            {!isConnected ? (
                <div style={{
                    background: 'rgba(255,255,255,0.05)',
                    padding: '3rem',
                    borderRadius: '16px',
                    textAlign: 'center',
                    border: '1px solid var(--glass-border)'
                }}>
                    <Cloud size={64} style={{ marginBottom: '1rem', opacity: 0.5 }} />
                    <h3>Connect to Cloud Provider</h3>
                    <p style={{ marginBottom: '2rem', color: 'var(--text-muted)' }}>
                        Link your Google Drive account to enable auto-sorting and cleanup features.
                    </p>
                    <button
                        onClick={handleLogin}
                        className="btn btn-primary"
                        disabled={isLoading}
                        style={{ fontSize: '1.1rem', padding: '0.8rem 2rem' }}
                    >
                        {isLoading ? 'Connecting...' : 'Login with Google'}
                    </button>
                </div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 1fr) 400px', gap: '2rem' }}>

                    {/* Controls & File List */}
                    <div>
                        <div style={{
                            display: 'flex',
                            gap: '1rem',
                            marginBottom: '2rem',
                            flexWrap: 'wrap'
                        }}>
                            <button
                                onClick={() => runAction('auto-sort', 'Auto-Sort')}
                                className="btn"
                                disabled={isLoading}
                                style={{ background: '#3b82f6', color: 'white', flex: 1 }}
                            >
                                <Play size={18} style={{ marginRight: '8px' }} /> Run Auto-Sort
                            </button>
                            <button
                                onClick={() => runAction('clean', 'Repository Clean')}
                                className="btn"
                                disabled={isLoading}
                                style={{ background: '#f59e0b', color: 'black', flex: 1 }}
                            >
                                <Layers size={18} style={{ marginRight: '8px' }} /> Clean Repo
                            </button>
                            <button
                                onClick={() => runAction('deduplicate', 'Deduplication')}
                                className="btn"
                                disabled={isLoading}
                                style={{ background: '#ef4444', color: 'white', flex: 1 }}
                            >
                                <Trash2 size={18} style={{ marginRight: '8px' }} /> Deduplicate
                            </button>
                        </div>

                        <div className="card">
                            <div style={{ padding: '1rem', borderBottom: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between' }}>
                                <h4 style={{ margin: 0 }}>Repository Files ({files.length})</h4>
                            </div>
                            <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
                                {files.length === 0 ? (
                                    <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>No files found</div>
                                ) : (
                                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                        <thead>
                                            <tr style={{ background: 'rgba(255,255,255,0.02)', textAlign: 'left' }}>
                                                <th style={{ padding: '0.8rem' }}>Name</th>
                                                <th style={{ padding: '0.8rem' }}>Created</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {files.map(f => (
                                                <tr key={f.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                                    <td style={{ padding: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                        <FileCheck size={16} color="#3b82f6" /> {f.name}
                                                    </td>
                                                    <td style={{ padding: '0.8rem', opacity: 0.7, fontSize: '0.9rem' }}>
                                                        {f.createdTime ? new Date(f.createdTime).toLocaleDateString() : '-'}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Status Monitor / Logs */}
                    <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '600px' }}>
                        <div style={{ padding: '1rem', borderBottom: '1px solid var(--glass-border)' }}>
                            <h4 style={{ margin: 0 }}>Status Monitor</h4>
                        </div>
                        <div style={{
                            flex: 1,
                            overflowY: 'auto',
                            padding: '1rem',
                            fontFamily: 'monospace',
                            fontSize: '0.9rem',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.5rem'
                        }}>
                            {logs.length === 0 && <span style={{ opacity: 0.5 }}>System ready.</span>}
                            {logs.map((l, i) => (
                                <div key={i} style={{
                                    opacity: l.type === 'error' ? 1 : 0.8,
                                    color: l.type === 'error' ? '#f87171' : 'inherit'
                                }}>
                                    <span style={{ opacity: 0.5 }}>[{l.time}]</span> {l.msg}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CloudManager;
