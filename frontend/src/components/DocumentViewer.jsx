import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, FileText, Download, Star, History, Info, ChevronRight, ChevronLeft } from 'lucide-react';

const DocumentViewer = ({ doc, onClose, isAdmin, user_id }) => {
    const [activeTab, setActiveTab] = useState('metadata');
    const [versions, setVersions] = useState([]);
    const [auditLogs, setAuditLogs] = useState([]);
    const [isFavorite, setIsFavorite] = useState(doc.is_favorite === 1);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [vRes, aRes] = await Promise.all([
                    axios.get(`http://localhost:5000/documents/${doc.id}/versions`),
                    axios.get(`http://localhost:5000/audit/document/${doc.id}`)
                ]);
                setVersions(vRes.data);
                setAuditLogs(aRes.data);
            } catch (err) {
                console.error("Failed to fetch document details", err);
            }
        };
        fetchData();
    }, [doc.id]);

    const handleToggleFavorite = async () => {
        try {
            const res = await axios.post(`http://localhost:5000/favorites?user_id=${user_id}`, { document_id: doc.id });
            setIsFavorite(res.data.is_favorite);
        } catch (err) {
            console.error("Failed to toggle favorite", err);
        }
    };

    const handleDownload = async () => {
        try {
            const response = await axios({
                url: `http://localhost:5000/documents/download/${doc.id}?is_admin=${isAdmin}&user_id=${user_id}`,
                method: 'GET',
                responseType: 'blob',
            });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', doc.filename);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            alert("Download failed. You may not have permissions for this file.");
        }
    };

    const isPDF = doc.filename.toLowerCase().endsWith('.pdf');
    const isImage = /\.(jpg|jpeg|png|gif)$/i.test(doc.filename);
    const fileUrl = `http://localhost:5000/uploads/${doc.filename}`; // This assumes static serving or proxy

    return (
        <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(15, 23, 42, 0.95)',
            backdropFilter: 'blur(10px)',
            zIndex: 1000,
            display: 'flex',
            flexDirection: 'column'
        }}>
            {/* Header */}
            <div style={{
                padding: '1rem 2rem', borderBottom: '1px solid var(--glass-border)',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <FileText color="var(--primary)" size={24} />
                    <h2 style={{ margin: 0, fontSize: '1.2rem' }}>{doc.filename}</h2>
                    <span style={{
                        fontSize: '0.8rem', background: 'rgba(255,255,255,0.1)',
                        padding: '0.2rem 0.5rem', borderRadius: '4px', color: 'var(--text-muted)'
                    }}>{doc.category}</span>
                </div>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <button onClick={handleToggleFavorite} className="btn-ghost" style={{ color: isFavorite ? '#eab308' : 'white' }}>
                        <Star fill={isFavorite ? '#eab308' : 'none'} size={20} />
                    </button>
                    <button onClick={handleDownload} className="btn" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Download size={18} /> Download
                    </button>
                    <button onClick={onClose} className="btn-ghost" style={{ padding: '0.5rem' }}>
                        <X size={24} />
                    </button>
                </div>
            </div>

            {/* Split Screen Body */}
            <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
                {/* Left: Viewer */}
                <div style={{ flex: 1, background: '#1e293b', position: 'relative', display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '2rem' }}>
                    {isPDF ? (
                        <iframe
                            src={`${fileUrl}#toolbar=0`}
                            title="PDF Viewer"
                            style={{ width: '100%', height: '100%', border: 'none', borderRadius: '8px', background: 'white' }}
                        />
                    ) : isImage ? (
                        <img src={fileUrl} alt="Document" style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', boxShadow: '0 10px 30px rgba(0,0,0,0.5)' }} />
                    ) : (
                        <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                            <FileText size={64} style={{ marginBottom: '1rem', opacity: 0.5 }} />
                            <p>Preview not available for this file type.</p>
                        </div>
                    )}
                </div>

                {/* Right: Sidebar */}
                <div style={{
                    width: '400px', background: 'rgba(255,255,255,0.02)',
                    borderLeft: '1px solid var(--glass-border)',
                    display: 'flex', flexDirection: 'column'
                }}>
                    <div style={{ display: 'flex', borderBottom: '1px solid var(--glass-border)' }}>
                        {['metadata', 'versions', 'audit'].map(tab => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                style={{
                                    flex: 1, padding: '1rem', background: 'none', border: 'none', color: activeTab === tab ? 'var(--primary)' : 'var(--text-muted)',
                                    borderBottom: activeTab === tab ? '2px solid var(--primary)' : 'none', cursor: 'pointer', fontSize: '0.9rem', fontWeight: activeTab === tab ? 'bold' : 'normal'
                                }}
                            >
                                {tab.charAt(0).toUpperCase() + tab.slice(1)}
                            </button>
                        ))}
                    </div>

                    <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem' }}>
                        {activeTab === 'metadata' && (
                            <div className="animate-fade-in">
                                <section style={{ marginBottom: '2rem' }}>
                                    <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Taxonomy Path</label>
                                    <div style={{ fontSize: '1rem', marginTop: '0.5rem', color: '#60a5fa' }}>
                                        {doc.subsidiary} / {doc.department} / {doc.function}
                                    </div>
                                </section>

                                <section style={{ marginBottom: '2rem' }}>
                                    <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Lifecycle Status</label>
                                    <div style={{ marginTop: '0.5rem' }}>
                                        <span style={{
                                            background: doc.approval_status === 'Approved' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(234, 179, 8, 0.2)',
                                            color: doc.approval_status === 'Approved' ? '#4ade80' : '#facc15',
                                            padding: '0.4rem 0.8rem', borderRadius: '20px', fontSize: '0.85rem'
                                        }}>
                                            {doc.approval_status || 'Pending'}
                                        </span>
                                    </div>
                                </section>

                                <section>
                                    <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Metadata Details</label>
                                    <pre style={{
                                        marginTop: '0.5rem', background: 'rgba(0,0,0,0.3)',
                                        padding: '1rem', borderRadius: '8px', fontSize: '0.85rem',
                                        color: '#e2e8f0', overflowX: 'auto'
                                    }}>
                                        {doc.metadata ? JSON.stringify(JSON.parse(doc.metadata), null, 2) : "No metadata available"}
                                    </pre>
                                </section>
                            </div>
                        )}

                        {activeTab === 'versions' && (
                            <div className="animate-fade-in">
                                {versions.length > 0 ? versions.map(v => (
                                    <div key={v.id} style={{
                                        padding: '1rem', background: 'rgba(255,255,255,0.03)',
                                        borderRadius: '8px', marginBottom: '1rem', border: '1px solid var(--glass-border)'
                                    }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                            <span style={{ fontWeight: 'bold' }}>{v.version_timestamp}</span>
                                            <span style={{ color: 'var(--primary)', fontSize: '0.8rem' }}>{v.category}</span>
                                        </div>
                                        <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{v.reason}</div>
                                        <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', opacity: 0.6 }}>by {v.user_id}</div>
                                    </div>
                                )) : <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '2rem' }}>No version history.</div>}
                            </div>
                        )}

                        {activeTab === 'audit' && (
                            <div className="animate-fade-in">
                                {auditLogs.length > 0 ? auditLogs.map(log => (
                                    <div key={log.id} style={{
                                        padding: '1rem', borderLeft: '2px solid var(--primary)',
                                        background: 'rgba(255,255,255,0.02)', marginBottom: '1rem'
                                    }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                            <span style={{ color: 'var(--primary)', fontWeight: 'bold', fontSize: '0.9rem' }}>{log.action}</span>
                                            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{log.timestamp}</span>
                                        </div>
                                        <div style={{ fontSize: '0.85rem' }}>{log.details}</div>
                                        <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', opacity: 0.6 }}>Actor: {log.performed_by}</div>
                                    </div>
                                )) : <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '2rem' }}>No audit logs.</div>}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DocumentViewer;
