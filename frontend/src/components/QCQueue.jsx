import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Microscope, CheckCircle, XCircle, AlertTriangle, FileText } from 'lucide-react';

const QCQueue = () => {
    const [queue, setQueue] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedBatch, setSelectedBatch] = useState(null);
    const [batchDocs, setBatchDocs] = useState([]);
    const [reviewNotes, setReviewNotes] = useState('');

    useEffect(() => {
        fetchQueue();
    }, []);

    const fetchQueue = async () => {
        try {
            const res = await axios.get('http://localhost:5000/qc/queue');
            setQueue(res.data);
        } catch (err) {
            console.error("Failed to load queue", err);
        } finally {
            setLoading(false);
        }
    };

    const handleReview = async (batch) => {
        setSelectedBatch(batch);
        setReviewNotes('');
        setLoading(true);
        try {
            // Fetch documents for this batch
            const res = await axios.get(`http://localhost:5000/documents?batch_id=${batch.id}`);
            // Note: I might need to update the /documents endpoint to filter by batch_id
            // Let's assume for now it works or I'll fix the backend filter
            setBatchDocs(res.data.filter(d => d.batch_id == batch.id));
        } catch (err) {
            console.error("Failed to load batch docs", err);
        } finally {
            setLoading(false);
        }
    };

    const submitReview = async (status) => {
        if (!selectedBatch) return;
        try {
            await axios.post(`http://localhost:5000/qc/batch/${selectedBatch.id}/review`, {
                status,
                notes: reviewNotes,
                user: 'QA_Specialist'
            });
            setSelectedBatch(null);
            fetchQueue();
        } catch (err) {
            alert("Review Failed: " + err.message);
        }
    };

    const publishDoc = async (docId) => {
        try {
            await axios.post(`http://localhost:5000/documents/${docId}/publish?user=QA_Specialist`);
            // Refresh docs
            handleReview(selectedBatch);
        } catch (err) {
            alert("Publishing Failed");
        }
    };

    const triggerRescan = async (docId) => {
        const reason = prompt("Enter rescan reason:");
        if (!reason) return;
        try {
            await axios.post(`http://localhost:5000/documents/${docId}/rescan`, {
                reason,
                user: 'QA_Specialist'
            });
            alert("Rescan triggered. Document status reset.");
            handleReview(selectedBatch);
        } catch (err) {
            alert("Rescan Failed");
        }
    };

    return (
        <div className="glass-panel" style={{ padding: '2rem' }}>
            <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Microscope size={24} /> Quality Control Queue
            </h2>

            {loading && !selectedBatch ? (
                <p>Loading queue...</p>
            ) : queue.length === 0 ? (
                <p style={{ color: 'var(--text-muted)' }}>No batches pending review.</p>
            ) : (
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Batch ID</th>
                                <th>Container</th>
                                <th>Start Time</th>
                                <th>Expected / Scanned</th>
                                <th>Status</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {queue.map(batch => (
                                <tr key={batch.id}>
                                    <td>#{batch.id}</td>
                                    <td>{batch.container_id}</td>
                                    <td>{batch.start_time}</td>
                                    <td>
                                        <span style={{
                                            color: batch.total_pages_scanned === batch.physical_page_count_expected ? '#4ade80' : '#f87171'
                                        }}>
                                            {batch.physical_page_count_expected} / {batch.total_pages_scanned}
                                        </span>
                                    </td>
                                    <td>{batch.status}</td>
                                    <td>
                                        <button className="btn" onClick={() => handleReview(batch)}>
                                            Review
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Review Modal / Sidebar Overlay */}
            {selectedBatch && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.8)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000
                }}>
                    <div className="glass-panel" style={{ width: '850px', maxWidth: '95%', padding: '2rem', background: '#1e293b', maxHeight: '90vh', overflowY: 'auto' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                            <h3>Review Batch #{selectedBatch.id}</h3>
                            <button onClick={() => setSelectedBatch(null)} style={{ background: 'none', border: 'none', color: 'white', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
                        </div>

                        <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                            Container: {selectedBatch.container_id}
                        </p>

                        <div style={{ marginBottom: '1.5rem' }}>
                            <h4>Documents in Batch</h4>
                            <div style={{ maxHeight: '300px', overflowY: 'auto', border: '1px solid var(--glass-border)', borderRadius: '8px', marginTop: '0.5rem' }}>
                                <table style={{ marginBottom: 0 }}>
                                    <thead>
                                        <tr>
                                            <th>Filename</th>
                                            <th>Category</th>
                                            <th>OCR</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {batchDocs.map(doc => {
                                            const isReady = doc.ocr_status === 'Completed' && doc.category && doc.category !== 'Unclassified';
                                            const isPublished = doc.is_published === 1;

                                            return (
                                                <tr key={doc.id}>
                                                    <td style={{ fontSize: '0.9rem' }}>{doc.filename}</td>
                                                    <td>{doc.category}</td>
                                                    <td>
                                                        <span style={{ color: doc.ocr_status === 'Completed' ? '#4ade80' : '#f87171' }}>
                                                            {doc.ocr_status}
                                                        </span>
                                                    </td>
                                                    <td style={{ display: 'flex', gap: '0.5rem' }}>
                                                        <button
                                                            className="btn btn-ghost"
                                                            style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                                                            onClick={() => triggerRescan(doc.id)}
                                                        >
                                                            Rescan
                                                        </button>
                                                        <button
                                                            className="btn"
                                                            disabled={!isReady || isPublished}
                                                            style={{
                                                                padding: '0.25rem 0.5rem',
                                                                fontSize: '0.75rem',
                                                                background: isPublished ? '#4ade80' : (isReady ? 'var(--primary)' : '#475569')
                                                            }}
                                                            onClick={() => publishDoc(doc.id)}
                                                        >
                                                            {isPublished ? 'Published' : 'Publish'}
                                                        </button>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                        {batchDocs.length === 0 && (
                                            <tr><td colSpan="4" style={{ textAlign: 'center', padding: '1rem' }}>No documents found for this batch.</td></tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '1.5rem' }}>
                            <div>
                                <h4>QC Checklist</h4>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
                                    <label><input type="checkbox" /> Readability (OCR Clear)</label>
                                    <label><input type="checkbox" /> Rotation (Pages Upright)</label>
                                    <label><input type="checkbox" /> Completeness (Page Count Matches)</label>
                                </div>
                            </div>
                            <div>
                                <h4>Review Notes</h4>
                                <textarea
                                    className="input"
                                    style={{ width: '100%', height: '80px', marginTop: '0.5rem' }}
                                    placeholder="Enter rejection reason or approval notes..."
                                    value={reviewNotes}
                                    onChange={e => setReviewNotes(e.target.value)}
                                />
                            </div>
                        </div>

                        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                            <button
                                className="btn"
                                style={{ background: '#ef4444', borderColor: '#ef4444' }}
                                onClick={() => submitReview('Returned')}
                            >
                                <XCircle size={18} style={{ marginRight: '0.5rem' }} /> Reject / Return
                            </button>

                            <button
                                className="btn"
                                style={{ background: '#22c55e', borderColor: '#22c55e' }}
                                onClick={() => submitReview('Archived')}
                            >
                                <CheckCircle size={18} style={{ marginRight: '0.5rem' }} /> Approve / Archive
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default QCQueue;
