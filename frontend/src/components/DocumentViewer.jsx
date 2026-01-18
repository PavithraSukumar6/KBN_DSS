import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, FileText, Download, Star, History, Info, ChevronRight, ChevronLeft } from 'lucide-react';

const DocumentViewer = ({ doc: initialDoc, onClose, isAdmin, user_id }) => {
    const [currentDoc, setCurrentDoc] = useState(initialDoc);
    const [activeTab, setActiveTab] = useState('metadata');
    const [versions, setVersions] = useState([]);
    const [auditLogs, setAuditLogs] = useState([]);
    const [isFavorite, setIsFavorite] = useState(initialDoc.is_favorite === 1);
    const [loading, setLoading] = useState(false);
    const [uploadingVersion, setUploadingVersion] = useState(false);

    useEffect(() => {
        let isActive = true;
        const requestId = Math.random().toString(36).substring(7);
        console.log(`[Viewer] Fetching data for ID: ${currentDoc.id} (ReqID: ${requestId})`);

        const fetchData = async () => {
            try {
                const [vRes, aRes] = await Promise.all([
                    axios.get(`http://localhost:5000/documents/${currentDoc.id}/versions`),
                    axios.get(`http://localhost:5000/audit/document/${currentDoc.id}`)
                ]);

                if (isActive) {
                    setVersions(vRes.data);
                    setAuditLogs(aRes.data);
                }
            } catch (err) {
                if (isActive) console.error("Failed to fetch document details", err);
            }
        };
        fetchData();

        return () => { isActive = false; };
    }, [currentDoc.id]);

    const handleVersionSwitch = async (versionDocId) => {
        if (versionDocId === currentDoc.id) return;
        setLoading(true);
        try {
            const res = await axios.get(`http://localhost:5000/documents/${versionDocId}/details`);
            setCurrentDoc(res.data);
            setIsFavorite(res.data.is_favorite === 1); // Reset favorite state for new doc
        } catch (err) {
            console.error("Failed to load version details", err);
            alert("Could not load version details.");
        } finally {
            setLoading(false);
        }
    };

    const handleUploadVersion = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploadingVersion(true);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('parent_doc_id', currentDoc.id); // Parent ID logic handled by backend (will resolve to root)
        formData.append('uploader_id', user_id);
        formData.append('container_id', currentDoc.container_id || '');
        formData.append('category', currentDoc.category); // Preserve category
        // Preserve other metadata if needed, or let backend handle defaults

        try {
            await axios.post('http://localhost:5000/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            alert("New version uploaded successfully!");
            // Refresh logic: The upload endpoint returns the new doc details usually?
            // Actually app.py /upload returns { documents: [...] }
            // Ideally we re-fetch the latest version via the versions list or just reload.
            // Let's reload the versions list, find the new top one, and switch to it.
            const vRes = await axios.get(`http://localhost:5000/documents/${currentDoc.id}/versions`);
            setVersions(vRes.data);
            // Switch to latest (first in list hopefully)
            if (vRes.data.length > 0) {
                handleVersionSwitch(vRes.data[0].id);
            }
        } catch (err) {
            console.error(err);
            alert("Failed to upload new version.");
        } finally {
            setUploadingVersion(false);
        }
    };

    const handleToggleFavorite = async () => {
        try {
            const res = await axios.post(`http://localhost:5000/favorites?user_id=${user_id}`, { document_id: currentDoc.id });
            setIsFavorite(res.data.is_favorite);
        } catch (err) {
            console.error("Failed to toggle favorite", err);
        }
    };

    const handleDownload = async () => {
        try {
            const response = await axios({
                url: `http://localhost:5000/documents/download/${currentDoc.id}?is_admin=${isAdmin}&user_id=${user_id}`,
                method: 'GET',
                responseType: 'blob',
            });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', currentDoc.filename);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            alert("Download failed.");
        }
    };

    const isPDF = currentDoc.filename.toLowerCase().endsWith('.pdf');
    const isImage = /\.(jpg|jpeg|png|gif)$/i.test(currentDoc.filename);
    const fileUrl = `http://localhost:5000/view/${currentDoc.id}?user_id=${user_id}`;

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
                    <div>
                        <h2 style={{ margin: 0, fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            {currentDoc.filename}
                            {currentDoc.version_number > 1 && <span style={{ fontSize: '0.8rem', background: 'var(--primary)', color: 'white', borderRadius: '4px', padding: '0 4px' }}>V{currentDoc.version_number}</span>}
                        </h2>
                        {currentDoc.status === 'Superseded' && <span style={{ color: '#f87171', fontSize: '0.8rem' }}>Superseded</span>}
                    </div>
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
                    {loading ? <div className="spin">Loading...</div> : (
                        isPDF ? (
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
                        )
                    )}
                </div>

                {/* Right: Sidebar */}
                <div style={{
                    width: '400px', background: 'rgba(255,255,255,0.02)',
                    borderLeft: '1px solid var(--glass-border)',
                    display: 'flex', flexDirection: 'column'
                }}>
                    <div style={{ display: 'flex', borderBottom: '1px solid var(--glass-border)' }}>
                        {['metadata', 'versions', 'history'].map(tab => (
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
                                        {currentDoc.subsidiary} / {currentDoc.department} / {currentDoc.function}
                                    </div>
                                </section>

                                <section style={{ marginBottom: '2rem' }}>
                                    <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Lifecycle Status</label>
                                    <div style={{ marginTop: '0.5rem' }}>
                                        <span style={{
                                            background: currentDoc.approval_status === 'Approved' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(234, 179, 8, 0.2)',
                                            color: currentDoc.approval_status === 'Approved' ? '#4ade80' : '#facc15',
                                            padding: '0.4rem 0.8rem', borderRadius: '20px', fontSize: '0.85rem'
                                        }}>
                                            {currentDoc.approval_status || 'Pending'}
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
                                        {currentDoc.metadata ? JSON.stringify(JSON.parse(currentDoc.metadata), null, 2) : "No metadata available"}
                                    </pre>
                                </section>
                            </div>
                        )}

                        {activeTab === 'versions' && (
                            <div className="animate-fade-in">
                                <div style={{ marginBottom: '1rem' }}>
                                    <label htmlFor="new-version-upload" className="btn" style={{ display: 'block', textAlign: 'center', background: '#3b82f6', cursor: 'pointer' }}>
                                        {uploadingVersion ? 'Uploading...' : 'Upload New Version'}
                                    </label>
                                    <input
                                        id="new-version-upload"
                                        type="file"
                                        style={{ display: 'none' }}
                                        onChange={handleUploadVersion}
                                        disabled={uploadingVersion}
                                    />
                                </div>
                                {versions.length > 0 ? versions.map(v => (
                                    <div key={v.id} onClick={() => handleVersionSwitch(v.id)} style={{
                                        padding: '1rem', background: v.id === currentDoc.id ? 'rgba(59, 130, 246, 0.1)' : 'rgba(255,255,255,0.03)',
                                        borderRadius: '8px', marginBottom: '1rem', border: v.id === currentDoc.id ? '1px solid #3b82f6' : '1px solid var(--glass-border)',
                                        cursor: 'pointer', transition: 'all 0.2s'
                                    }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                            <span style={{ fontWeight: 'bold' }}>V{v.version_number} <span style={{ fontSize: '0.8rem', fontWeight: 'normal', color: 'var(--text-muted)' }}>({v.status})</span></span>
                                            <span style={{ color: 'var(--primary)', fontSize: '0.8rem' }}>{v.upload_date ? v.upload_date.split(' ')[0] : ''}</span>
                                        </div>
                                        <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{v.filename}</div>
                                        <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', opacity: 0.6 }}>by {v.uploader_id}</div>
                                    </div>
                                )) : <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '2rem' }}>No version history.</div>}
                            </div>
                        )}

                        {activeTab === 'history' && (
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
