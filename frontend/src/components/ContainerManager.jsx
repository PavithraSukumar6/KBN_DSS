import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Package, Truck, History, Search } from 'lucide-react';
import FolderTree from './FolderTree';

const ContainerManager = ({ refreshTrigger }) => {
    const [containers, setContainers] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchContainers();
    }, [refreshTrigger]);

    const fetchContainers = async () => {
        setLoading(true);
        try {
            const res = await axios.get('http://localhost:5000/containers');
            // Ensure we handle non-array responses gracefully
            setContainers(Array.isArray(res.data) ? res.data : []);
        } catch (error) {
            console.error("Error fetching containers", error);
            setContainers([]);
        } finally {
            setLoading(false);
        }
    };

    const selectedContainer = containers.find(c => c.id === selectedId);

    const [error, setError] = useState(null);
    const [transferMode, setTransferMode] = useState(false);
    const [historyMode, setHistoryMode] = useState(false);
    const [newLocation, setNewLocation] = useState('');
    const [historyLogs, setHistoryLogs] = useState([]);

    const handleTransferClick = () => {
        setTransferMode(!transferMode);
        setHistoryMode(false);
        setNewLocation(selectedContainer?.source_location || '');
        setError(null);
    };

    const handleHistoryClick = async () => {
        if (historyMode) {
            setHistoryMode(false);
            return;
        }
        setTransferMode(false);
        setLoading(true);
        try {
            const res = await axios.get(`http://localhost:5000/containers/${selectedContainer.id}/history`);
            setHistoryLogs(res.data);
            setHistoryMode(true);
        } catch (err) {
            console.error(err);
            setError("Failed to fetch history");
        } finally {
            setLoading(false);
        }
    };

    const confirmTransfer = async () => {
        if (!newLocation.trim()) return;
        setLoading(true);
        try {
            await axios.post(`http://localhost:5000/containers/${selectedContainer.id}/transfer`, {
                location: newLocation,
                user: 'Gokul_Admin'
            });
            setTransferMode(false);
            fetchContainers();
        } catch (err) {
            setError("Transfer failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="glass-panel" style={{ padding: '2rem', minHeight: '500px' }}>
            <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Package size={24} /> Container Hierarchy
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(200px, 1fr) 1.5fr', gap: '2rem' }}>
                {/* Tree View Section */}
                <div style={{ borderRight: '1px solid var(--glass-border)', paddingRight: '1rem' }}>
                    {loading && !selectedContainer ? (
                        <p style={{ color: 'var(--text-muted)' }}>Loading hierarchy...</p>
                    ) : containers.length === 0 ? (
                        <p style={{ color: 'var(--text-muted)' }}>No containers yet.</p>
                    ) : (
                        <FolderTree
                            containers={containers}
                            onSelect={(id) => { setSelectedId(id); setTransferMode(false); setHistoryMode(false); setError(null); }}
                            selectedId={selectedId}
                        />
                    )}
                </div>

                {/* Details Section */}
                <div>
                    {selectedContainer ? (
                        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--primary)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                                <div>
                                    <h3 style={{ margin: 0, fontSize: '1.4rem' }}>{selectedContainer.name || selectedContainer.id}</h3>
                                    <p style={{ color: 'var(--text-muted)', margin: '0.25rem 0' }}>ID: {selectedContainer.id}</p>
                                    <code style={{ background: 'rgba(0,0,0,0.3)', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.8rem', color: '#60a5fa' }}>
                                        {selectedContainer.barcode || 'NO-BARCODE'}
                                    </code>
                                </div>
                                <div style={{ textAlign: 'right', fontSize: '0.9rem' }}>
                                    <div style={{ color: 'var(--text-muted)' }}>{selectedContainer.status || 'Active'}</div>
                                    <div>{selectedContainer.created_at?.split(' ')[0]}</div>
                                </div>
                            </div>

                            <hr style={{ border: 'none', borderTop: '1px solid var(--glass-border)', margin: '1rem 0' }} />

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                                <div>
                                    <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Subsidiary</label>
                                    <div>{selectedContainer.subsidiary || 'N/A'}</div>
                                </div>
                                <div>
                                    <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Department</label>
                                    <div>{selectedContainer.department || 'N/A'}</div>
                                </div>
                                <div>
                                    <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Location</label>
                                    <div>{selectedContainer.source_location || 'Unknown'}</div>
                                </div>
                                <div>
                                    <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Confidentiality</label>
                                    <div>{selectedContainer.confidentiality_level || 'General'}</div>
                                </div>
                            </div>

                            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                                <button
                                    className={`btn ${transferMode ? 'active' : ''}`}
                                    style={{ flex: 1, padding: '0.6rem', background: transferMode ? 'var(--primary)' : '' }}
                                    onClick={handleTransferClick}
                                >
                                    <Truck size={16} /> Transfer
                                </button>
                                <button
                                    className={`btn ${historyMode ? 'active' : ''}`}
                                    style={{ flex: 1, padding: '0.6rem', background: historyMode ? 'var(--primary)' : '' }}
                                    onClick={handleHistoryClick}
                                >
                                    <History size={16} /> History
                                </button>
                            </div>

                            {error && (
                                <div style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', padding: '0.5rem', borderRadius: '6px', marginBottom: '1rem', fontSize: '0.9rem' }}>
                                    {error}
                                </div>
                            )}

                            {transferMode && (
                                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--glass-border)' }}>
                                    <label style={{ display: 'block', fontSize: '0.9rem', marginBottom: '0.5rem' }}>New Location / Shelf:</label>
                                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                                        <input
                                            type="text"
                                            value={newLocation}
                                            onChange={(e) => setNewLocation(e.target.value)}
                                            style={{ flex: 1, padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.05)', color: 'white' }}
                                        />
                                        <button className="btn" onClick={confirmTransfer} disabled={loading}>Confirm</button>
                                    </div>
                                </div>
                            )}

                            {historyMode && (
                                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--glass-border)', maxHeight: '200px', overflowY: 'auto' }}>
                                    <h4 style={{ marginTop: 0, marginBottom: '0.5rem' }}>History Log</h4>
                                    {historyLogs.length === 0 ? (
                                        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No history found.</p>
                                    ) : (
                                        <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '0.85rem' }}>
                                            {historyLogs.map((log, i) => (
                                                <li key={i} style={{ padding: '0.4rem 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                                    <div style={{ color: '#60a5fa' }}>{log.timestamp}</div>
                                                    <div>Moved to <b>{log.new_location}</b> by {log.transferred_by}</div>
                                                    <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Prev: {log.previous_location}</div>
                                                </li>
                                            ))}
                                        </ul>
                                    )}
                                </div>
                            )}

                        </div>
                    ) : (
                        <div style={{ textAlign: 'center', color: 'var(--text-muted)', paddingTop: '4rem' }}>
                            <Search size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                            <p>Select a container to view details</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ContainerManager;
