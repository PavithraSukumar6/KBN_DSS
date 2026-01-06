import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Trash2, RefreshCw, AlertTriangle, FileText, CheckCircle } from 'lucide-react';

const CleanupReviews = ({ currentUser }) => {
    const [deletedDocs, setDeletedDocs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState(null);

    useEffect(() => {
        fetchDeletedDocs();
    }, []);

    const fetchDeletedDocs = async () => {
        try {
            // Fetch all docs with 'Soft_Deleted' or 'Pending_Deletion' status
            // We can reuse the filter endpoint
            const res = await axios.get(`http://localhost:5000/documents?status=Soft_Deleted&is_admin=true`);
            const res2 = await axios.get(`http://localhost:5000/documents?status=Pending_Deletion&is_admin=true`);

            // Combine and dedup
            const allDocs = [...res.data, ...res2.data];
            // Remove duplicates just in case
            const unique = Array.from(new Set(allDocs.map(a => a.id)))
                .map(id => allDocs.find(a => a.id === id));

            setDeletedDocs(unique);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleRestore = async (docId) => {
        try {
            await axios.post(`http://localhost:5000/documents/${docId}/restore?user_id=${currentUser?.id}`);
            setMessage({ type: 'success', text: 'Document restored successfully' });
            fetchDeletedDocs();
        } catch (err) {
            setMessage({ type: 'error', text: err.response?.data?.error || 'Restore failed' });
        }
    };

    const handlePermanentDelete = async (docId) => {
        if (!window.confirm("Are you sure? This action CANNOT be undone.")) return;

        try {
            await axios.delete(`http://localhost:5000/documents/${docId}?permanent=true&is_admin=true&user_id=${currentUser?.id}`);
            setMessage({ type: 'success', text: 'Document permanently destroyed' });
            fetchDeletedDocs();
        } catch (err) {
            setMessage({ type: 'error', text: err.response?.data?.error || 'Deletion failed' });
        }
    };

    if (loading) return <div className="glass-panel" style={{ padding: '2rem' }}>Loading Cleanup Queue...</div>;

    return (
        <div className="container animate-fade-in">
            <div className="glass-panel" style={{ padding: '2rem', marginBottom: '2rem' }}>
                <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                    <Trash2 size={24} color="#f87171" /> Cleanup Review Queue
                </h2>
                <p style={{ color: 'var(--text-muted)' }}>
                    Review documents marked for deletion. "Pending Deletion" items are expired retention files waiting for approval.
                    "Soft Deleted" items are manually deleted files in the recycling bin.
                </p>
            </div>

            {message && (
                <div style={{
                    marginBottom: '1.5rem', padding: '1rem', borderRadius: '8px',
                    background: message.type === 'success' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                    color: message.type === 'success' ? '#4ade80' : '#f87171',
                    border: `1px solid ${message.type === 'success' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
                }}>
                    {message.text}
                </div>
            )}

            <div style={{ display: 'grid', gap: '1rem' }}>
                {deletedDocs.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                        <CheckCircle size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                        <p>No documents pending cleanup.</p>
                    </div>
                ) : (
                    deletedDocs.map(doc => (
                        <div key={doc.id} className="glass-panel" style={{ padding: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                <div style={{ background: 'rgba(255,255,255,0.05)', padding: '0.75rem', borderRadius: '8px' }}>
                                    <FileText size={24} color="var(--primary)" />
                                </div>
                                <div>
                                    <div style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>{doc.filename}</div>
                                    <div style={{ display: 'flex', gap: '1rem', fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                                        <span>Type: {doc.category}</span>
                                        <span>•</span>
                                        <span>Uploaded: {doc.upload_date}</span>
                                        <span>•</span>
                                        <span style={{
                                            color: doc.status === 'Pending_Deletion' ? '#facc15' : '#f87171',
                                            fontWeight: 'bold'
                                        }}>
                                            {doc.status.replace('_', ' ')}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <div style={{ display: 'flex', gap: '1rem' }}>
                                <button
                                    onClick={() => handleRestore(doc.id)}
                                    className="btn btn-ghost"
                                    style={{ color: '#4ade80' }}
                                    title="Restore to active library"
                                >
                                    <RefreshCw size={18} style={{ marginRight: '0.5rem' }} /> Restore
                                </button>
                                <button
                                    onClick={() => handlePermanentDelete(doc.id)}
                                    className="btn"
                                    style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.3)' }}
                                    title="Permanently Destroy"
                                >
                                    <Trash2 size={18} style={{ marginRight: '0.5rem' }} /> Destroy
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default CleanupReviews;
