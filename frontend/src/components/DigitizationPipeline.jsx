import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ScanLine, FileText, CheckCircle, AlertCircle, Scissors } from 'lucide-react';

import Upload from './Upload';

const DigitizationPipeline = ({ onUploadSuccess }) => {
    // State
    const [containers, setContainers] = useState([]);
    const [selectedContainer, setSelectedContainer] = useState('');
    const [activeBatch, setActiveBatch] = useState(null); // { id, expected, scanned, status }
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState(null);

    // Fetch containers on mount
    useEffect(() => {
        loadContainers();
    }, []);

    const loadContainers = async () => {
        try {
            const res = await axios.get('http://localhost:5000/containers');
            setContainers(Array.isArray(res.data) ? res.data : []);
        } catch (err) {
            console.error("Failed to load containers", err);
        }
    };

    const startBatch = async () => {
        if (!selectedContainer) return;
        setLoading(true);
        try {
            const res = await axios.post('http://localhost:5000/batches', {
                container_id: selectedContainer
            });
            setActiveBatch({
                id: res.data.batch_id,
                expected: res.data.expected_pages,
                scanned: 0,
                status: 'Pending'
            });
            setMessage({ type: 'success', text: 'Batch Started! Ready to Scan.' });
        } catch (err) {
            setMessage({ type: 'error', text: 'Failed to start batch.' });
        } finally {
            setLoading(false);
        }
    };

    const handleBatchUploadSuccess = () => {
        if (!activeBatch) return;
        checkCompleteness(activeBatch.id);
        if (onUploadSuccess) onUploadSuccess();
        setMessage({ type: 'success', text: 'Files queued for processing.' });
    };

    const checkCompleteness = async (batchId) => {
        try {
            const res = await axios.get(`http://localhost:5000/batches/${batchId}/completeness`);
            setActiveBatch(prev => ({
                ...prev,
                scanned: res.data.scanned,
                status: res.data.is_complete ? 'Completed' : 'Scanning'
            }));
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="glass-panel" style={{ padding: '2rem' }}>
            <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <ScanLine size={24} /> Digitization Pipeline
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                {/* Left Side: Container Selection & Batch Info */}
                <div>
                    {!activeBatch ? (
                        <div style={{ padding: '1.5rem', background: 'rgba(255,255,255,0.05)', borderRadius: '12px' }}>
                            <label className="label" style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Select Container to Digitize</label>
                            <select
                                className="input"
                                style={{ width: '100%', padding: '0.75rem', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--glass-border)', color: 'white', borderRadius: '8px', marginBottom: '1rem' }}
                                value={selectedContainer}
                                onChange={(e) => setSelectedContainer(e.target.value)}
                            >
                                <option value="">-- Select Container --</option>
                                {containers.map(c => (
                                    <option key={c.id} value={c.id}>
                                        {c.id} ({c.department} - {c.physical_page_count} pages est)
                                    </option>
                                ))}
                            </select>
                            <button
                                className="btn"
                                style={{ width: '100%' }}
                                onClick={startBatch}
                                disabled={!selectedContainer || loading}
                            >
                                {loading ? 'Starting...' : 'Start New Batch'}
                            </button>
                        </div>
                    ) : (
                        <div style={{ padding: '1.5rem', background: 'rgba(255,255,255,0.05)', borderRadius: '12px', border: '1px solid var(--primary)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                                <div>
                                    <h3 style={{ margin: 0 }}>Batch: {activeBatch.id}</h3>
                                    <p style={{ margin: '0.5rem 0 0', color: 'var(--text-muted)' }}>
                                        Container: <strong>{selectedContainer}</strong>
                                    </p>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                    <div style={{ fontSize: '2rem', fontWeight: 'bold', color: activeBatch.expected === activeBatch.scanned ? 'var(--success)' : 'white' }}>
                                        {activeBatch.scanned} / {activeBatch.expected}
                                    </div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Pages Scanned</div>
                                </div>
                            </div>
                            <div style={{
                                padding: '0.5rem',
                                borderRadius: '4px',
                                background: 'rgba(34, 197, 94, 0.1)',
                                color: 'var(--success)',
                                textAlign: 'center',
                                fontSize: '0.9rem',
                                border: '1px solid rgba(34, 197, 94, 0.2)',
                                marginBottom: '1rem'
                            }}>
                                Status: {activeBatch.status}
                            </div>
                            <button
                                className="btn btn-ghost"
                                style={{ width: '100%', border: '1px solid #3b82f6', color: '#60a5fa', display: 'flex', alignItems: 'center', gap: '0.4rem', justifyContent: 'center' }}
                                onClick={async () => {
                                    setLoading(true);
                                    try {
                                        const res = await axios.post('http://localhost:5000/scan/direct');
                                        setMessage({ type: 'success', text: `Scan Captured: ${res.data.filename}. Please upload the file from intake_temp.` });
                                    } catch (err) {
                                        setMessage({ type: 'error', text: 'Scan failed: ' + (err.response?.data?.error || err.message) });
                                    } finally {
                                        setLoading(false);
                                    }
                                }}
                                disabled={loading}
                            >
                                <ScanLine size={18} /> {loading ? "Scanning..." : "Direct Scan"}
                            </button>
                        </div>
                    )}

                    {/* Message Area */}
                    {message && (
                        <div style={{
                            marginTop: '1.5rem',
                            padding: '1rem',
                            borderRadius: '8px',
                            background: message.type === 'success' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                            color: message.type === 'success' ? '#4ade80' : '#f87171',
                            border: `1px solid ${message.type === 'success' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
                        }}>
                            {message.text}
                        </div>
                    )}
                </div>

                {/* Right Side: Upload Area (Always Visible) */}
                <div>
                    <Upload
                        containerId={selectedContainer}
                        batchId={activeBatch?.id}
                        onUploadSuccess={handleBatchUploadSuccess}
                    />
                </div>
            </div>
        </div>
    );
};

export default DigitizationPipeline;
