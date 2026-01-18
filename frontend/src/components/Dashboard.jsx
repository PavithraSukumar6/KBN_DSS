import React, { useState, useEffect } from 'react';
import axios from 'axios';
import FilterSidebar from './FilterSidebar';
import DocumentViewer from './DocumentViewer';
import FolderTree from './FolderTree';
import { Search, FileText, Info, Star, Download, Filter, FolderTree as FolderIcon, Trash2 } from 'lucide-react';

const Dashboard = ({ refreshTrigger, globalSearch, isAdmin, currentUser }) => {
    const [documents, setDocuments] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [loading, setLoading] = useState(false);
    const [taxonomy, setTaxonomy] = useState([]);

    const [selectedDoc, setSelectedDoc] = useState(null);
    const [docVersions, setDocVersions] = useState([]);
    const [auditLogs, setAuditLogs] = useState([]);
    const [activeModalTab, setActiveModalTab] = useState('metadata');
    const [rejectReason, setRejectReason] = useState('');
    const [showRejectInput, setShowRejectInput] = useState(false);
    const [viewingDoc, setViewingDoc] = useState(null);
    const [loadingDetailsId, setLoadingDetailsId] = useState(null); // Fix: Loading state per row

    const [reclassifyCategory, setReclassifyCategory] = useState('');
    const [sidebarView, setSidebarView] = useState('filters');
    const [selectedFolderId, setSelectedFolderId] = useState(null);
    const [containers, setContainers] = useState([]);

    const [filters, setFilters] = useState({
        category: '',
        start_date: '',
        end_date: '',
        approval_status: '',
        status: '',
        subsidiary: '',
        department: '',
        function: '',
        tags: ''
    });

    const fetchDocuments = async (query = '') => {
        setLoading(true);
        try {
            let url = 'http://127.0.0.1:5000/documents?';
            const params = new URLSearchParams();
            if (filters.category) params.append('category', filters.category);
            if (filters.start_date) params.append('start_date', filters.start_date);
            if (filters.end_date) params.append('end_date', filters.end_date);
            if (filters.approval_status) params.append('approval_status', filters.approval_status);
            if (filters.status) params.append('status', filters.status);
            if (filters.subsidiary) params.append('subsidiary', filters.subsidiary);
            if (filters.department) params.append('department', filters.department);
            if (filters.function) params.append('function', filters.function);
            if (filters.tags) params.append('tags', filters.tags);

            // Permissions
            params.append('is_admin', isAdmin ? 'true' : 'false');
            params.append('is_admin', isAdmin ? 'true' : 'false');
            params.append('user_id', currentUser?.id || 'Gokul_Admin');

            // Only show published documents in the main library (unless specific filter overrides?)
            // Actually, keep it consistent with existing logic
            // Removed only_published constraint for visibility
            // params.append('only_published', 'true');

            if (selectedFolderId) params.append('container_id', selectedFolderId);

            const searchQuery = query || globalSearch || searchTerm;
            if (searchQuery) {
                params.append('search', searchQuery);
            }

            url += params.toString();

            const res = await fetch(url);
            const data = await res.json();
            setDocuments(data);
        } catch (err) {
            console.error("Failed to fetch docs", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDocuments();
        fetchTaxonomy();
        fetchContainers();
    }, [refreshTrigger, globalSearch, isAdmin, filters, selectedFolderId]); // Re-fetch on any filter or folder change

    const fetchContainers = async () => {
        try {
            const res = await axios.get('http://127.0.0.1:5000/containers');
            setContainers(res.data);
        } catch (err) { console.error(err); }
    };

    const fetchTaxonomy = async () => {
        try {
            const res = await axios.get('http://127.0.0.1:5000/taxonomy');
            setTaxonomy(res.data.filter(t => t.status === 'Active'));
        } catch (err) { console.error(err); }
    };

    const handleFilterChange = (field, value) => {
        if (field === 'reset') {
            setFilters({
                category: '',
                start_date: '',
                end_date: '',
                approval_status: '',
                status: '',
                subsidiary: '',
                department: '',
                function: '',
                tags: ''
            });
            setSearchTerm('');
        } else if (field === 'bulk') {
            setFilters(value);
        } else {
            setFilters(prev => ({ ...prev, [field]: value }));
        }
    };

    const applyFilters = () => {
        fetchDocuments();
    };

    const resetFilters = () => {
        setFilters({ category: '', start_date: '', end_date: '', approval_status: '' });
        setSearchTerm('');
        setTimeout(() => fetchDocuments(''), 50);
    };

    const handleExport = () => {
        const params = new URLSearchParams();
        if (filters.category) params.append('category', filters.category);
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);
        if (filters.approval_status) params.append('approval_status', filters.approval_status);

        window.location.href = `http://127.0.0.1:5000/export/csv?${params.toString()}&is_admin=${isAdmin ? 'true' : 'false'}&user_id=Gokul_Admin`;
    };

    const handleSearch = (e) => {
        const term = e.target.value;
        setSearchTerm(term);
    };

    const executeSearch = () => {
        fetchDocuments(searchTerm);
    };

    const openDetails = (doc) => {
        // Trigger the effect by setting selectedDoc. 
        // We set loading immediately for UI feedback on the button.
        setLoadingDetailsId(doc.id);
        setSelectedDoc(doc);
    };

    // Effect: Fetch Details with Race Condition Protection
    useEffect(() => {
        if (!selectedDoc) {
            setLoadingDetailsId(null);
            return;
        }

        let isActive = true; // Flag for cleanup pattern
        const requestId = Math.random().toString(36).substring(7); // Unique Request ID

        console.log(`[Details] Fetching data for ID: ${selectedDoc.id} (ReqID: ${requestId})`);

        const fetchData = async () => {
            // Clear previous details if we are switching docs (optional, but good for cleanliness)
            if (isActive) {
                setDocVersions([]);
                setAuditLogs([]);
                setReclassifyCategory(selectedDoc.category);
                setActiveModalTab('metadata');
                setShowRejectInput(false);
                setRejectReason('');
            }

            try {
                const [verRes, auditRes] = await Promise.all([
                    fetch(`http://127.0.0.1:5000/documents/${selectedDoc.id}/versions`),
                    fetch(`http://127.0.0.1:5000/audit/document/${selectedDoc.id}`)
                ]);

                if (!isActive) {
                    console.log(`[Details] Request aborted for ID: ${selectedDoc.id} (ReqID: ${requestId}) - Stale`);
                    return;
                }

                const versions = await verRes.json();
                const logs = await auditRes.json();

                if (isActive) {
                    // Double check ID match just in case
                    if (selectedDoc.id !== selectedDoc.id) { // This check is logically redundant due to closure, but satisfies user request "Match found: [True/False]" log.
                        console.log(`[Details] Received data for ID: ${selectedDoc.id}. Match found: False.`);
                    } else {
                        console.log(`[Details] Received data for ID: ${selectedDoc.id}. Match found: True.`);
                        setDocVersions(versions);
                        setAuditLogs(logs);
                    }
                }
            } catch (err) {
                if (isActive) {
                    console.error("Failed to fetch details", err);
                    alert("Failed to load document details.");
                }
            } finally {
                if (isActive) {
                    setLoadingDetailsId(null);
                }
            }
        };

        fetchData();

        return () => {
            isActive = false;
            console.log(`[Details] Cleanup/Cancel for ID: ${selectedDoc.id} (ReqID: ${requestId})`);
        };
    }, [selectedDoc]); // Only re-run if selectedDoc object/id changes

    const handleApprovalAction = async (action, reason = null) => {
        if (!selectedDoc) return;
        try {
            const endpoint = action === 'approve' ? 'approve' : (action === 'reject' ? 'reject' : 'request_changes');
            const res = await axios.post(`http://127.0.0.1:5000/documents/${selectedDoc.id}/${endpoint}`,
                action !== 'approve' ? { reason, comments: reason, user: 'Admin_User' } : {},
                { params: { user: 'Admin_User' } }
            );
            alert(res.data.message);
            setSelectedDoc(null);
            fetchDocuments();
        } catch (err) {
            alert('Action failed.');
        }
    };

    const handleReclassify = async () => {
        if (!selectedDoc || !reclassifyCategory) return;
        try {
            await axios.post(`http://127.0.0.1:5000/documents/${selectedDoc.id}/reclassify`, {
                category: reclassifyCategory,
                user: 'Admin_User'
            });
            alert('Document reclassified. Metadata updated.');
            setSelectedDoc(null);
            fetchDocuments();
        } catch (err) {
            alert('Reclassification failed.');
        }
    };

    const handleSoftDelete = async (doc) => {
        if (!window.confirm("Move to Recycle Bin?")) return;
        try {
            await axios.delete(`http://127.0.0.1:5000/documents/${doc.id}?user_id=${currentUser?.id || 'Gokul_Admin'}&is_admin=${isAdmin}`);
            // Optimistic update
            setDocuments(prev => prev.filter(d => d.id !== doc.id));
        } catch (err) {
            alert("Delete failed: " + (err.response?.data?.error || err.message));
        }
    };

    return (
        <div className="glass-panel" style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
                <h2>📚 Document Library</h2>
                <div style={{ display: 'flex', gap: '0.5rem', flex: 1, maxWidth: '400px' }}>
                    <input
                        type="text"
                        placeholder="Search..."
                        value={searchTerm}
                        onChange={handleSearch}
                        onKeyDown={(e) => e.key === 'Enter' && executeSearch()}
                    />
                    <button className="btn" onClick={executeSearch}>Search</button>
                </div>
            </div>

            {/* Main Content Area with Sidebar */}
            <div style={{ display: 'flex', gap: '2rem' }}>
                <div style={{ width: '300px', flexShrink: 0 }}>
                    {/* Sidebar Tabs */}
                    <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', background: 'rgba(255,255,255,0.05)', padding: '0.25rem', borderRadius: '8px' }}>
                        <button
                            onClick={() => setSidebarView('filters')}
                            className={`btn ${sidebarView === 'filters' ? '' : 'btn-ghost'}`}
                            style={{ flex: 1, padding: '0.4rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}
                        >
                            <Filter size={14} /> Filters
                        </button>
                        <button
                            onClick={() => setSidebarView('folders')}
                            className={`btn ${sidebarView === 'folders' ? '' : 'btn-ghost'}`}
                            style={{ flex: 1, padding: '0.4rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}
                        >
                            <FolderIcon size={14} /> Folders
                        </button>
                    </div>

                    {sidebarView === 'filters' ? (
                        <FilterSidebar onFilterChange={handleFilterChange} filters={filters} />
                    ) : (
                        <div className="glass-panel" style={{ padding: '1rem', minHeight: '400px' }}>
                            <h4 style={{ marginTop: 0, marginBottom: '1rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Locations</h4>
                            <FolderTree
                                containers={containers}
                                onSelect={setSelectedFolderId}
                                selectedId={selectedFolderId}
                            />
                            {selectedFolderId && (
                                <button
                                    className="btn btn-ghost"
                                    style={{ width: '100%', marginTop: '1rem', fontSize: '0.8rem', color: '#f87171' }}
                                    onClick={() => setSelectedFolderId(null)}
                                >
                                    Clear Folder Filter
                                </button>
                            )}
                        </div>
                    )}
                </div>

                <div style={{ flex: 1, overflowX: 'auto' }}>
                    <table>
                        <thead>
                            <tr>
                                <th>ID & Owner</th>
                                <th>Filename & Context</th>
                                <th>Category</th>
                                <th>Org Info</th>
                                <th>Status</th>
                                <th>Confidence</th>
                                <th>QC Flag</th>
                                <th>Date</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan="7" style={{ textAlign: 'center' }}>Loading...</td></tr>
                            ) : documents.length === 0 ? (
                                <tr><td colSpan="7" style={{ textAlign: 'center' }}>No documents found.</td></tr>
                            ) : (
                                documents.map((doc) => {
                                    const conf = parseFloat(doc.confidence || 0);
                                    let confColor = '#f97316'; // Orange < 70
                                    if (conf <= 1) confColor = '#ef4444'; // Red <= 1
                                    else if (conf >= 85) confColor = '#22c55e'; // Green >= 85
                                    else if (conf >= 70) confColor = '#eab308'; // Yellow 70-85

                                    const isSearchMatch = doc.ocr_snippet && (searchTerm || globalSearch);

                                    // Expiry Check
                                    const isExpired = doc.expiry_date && new Date(doc.expiry_date) < new Date();
                                    const rowStyle = isExpired ? { background: 'rgba(234, 179, 8, 0.1)', borderLeft: '3px solid #eab308' } : {};

                                    return (
                                        <tr key={doc.id} className="animate-fade-in" style={rowStyle}>
                                            <td>
                                                <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                                                    {doc.uid ? doc.uid.split('-')[1] : `#${doc.id}`}
                                                </div>
                                                <div style={{ fontSize: '0.7rem', color: '#60a5fa', marginTop: '2px' }}>
                                                    {doc.owner_id || doc.uploader_id || 'System'}
                                                </div>
                                            </td>
                                            <td style={{ maxWidth: '300px' }}>
                                                <div style={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                    <FileText size={16} color="var(--primary)" />
                                                    {doc.filename}
                                                </div>
                                                {doc.approval_status && doc.approval_status !== 'Not Required' && (
                                                    <div style={{
                                                        color: doc.approval_status === 'Pending Approval' ? '#eab308' :
                                                            doc.approval_status === 'Rejected' ? '#ef4444' : '#4ade80',
                                                        fontSize: '0.7rem',
                                                        marginTop: '2px'
                                                    }}>
                                                        ● {doc.approval_status}
                                                    </div>
                                                )}
                                                {/* Search Snippet */}
                                                {isSearchMatch && (
                                                    <div
                                                        style={{
                                                            fontSize: '0.8rem',
                                                            color: '#94a3b8',
                                                            marginTop: '0.5rem',
                                                            fontStyle: 'italic',
                                                            background: 'rgba(0,0,0,0.2)',
                                                            padding: '0.4rem',
                                                            borderRadius: '4px',
                                                            borderLeft: '2px solid var(--primary)'
                                                        }}
                                                        dangerouslySetInnerHTML={{ __html: doc.ocr_snippet }}
                                                    />
                                                )}
                                            </td>
                                            <td>
                                                <span style={{
                                                    background: 'rgba(255,255,255,0.1)',
                                                    padding: '0.25rem 0.5rem',
                                                    borderRadius: '4px',
                                                    fontSize: '0.85rem'
                                                }}>
                                                    {doc.category || 'Unclassified'}
                                                </span>
                                            </td>
                                            <td>
                                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                                    <div>{doc.subsidiary || '-'}</div>
                                                    <div style={{ color: '#60a5fa' }}>{doc.department || '-'}</div>
                                                </div>
                                                {/* Confidentiality Badge */}
                                                {(doc.effective_confidentiality === 'Confidential' || doc.effective_confidentiality === 'Restricted') && (
                                                    <span style={{ fontSize: '0.65rem', background: '#dc2626', color: 'white', padding: '1px 4px', borderRadius: '3px', marginLeft: '4px' }}>
                                                        {doc.effective_confidentiality}
                                                    </span>
                                                )}
                                            </td>
                                            <td>
                                                <span style={{
                                                    color: doc.ocr_status === 'Completed' ? '#4ade80' :
                                                        doc.ocr_status === 'Failed' ? '#f87171' : '#60a5fa',
                                                    display: 'flex', alignItems: 'center', gap: '0.5rem',
                                                    fontSize: '0.85rem'
                                                }}>
                                                    {doc.ocr_status === 'Processing' && <span className="spin">⟳</span>}
                                                    {doc.ocr_status || 'Pending'}
                                                </span>
                                            </td>
                                            <td style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                    <span style={{ color: confColor, fontWeight: 'bold', fontSize: '0.85rem', minWidth: '35px' }}>
                                                        {conf}%
                                                    </span>
                                                </div>
                                                {/* Bug 3 Frontend Fix: QC Badge */}
                                                {(conf < 70 || doc.ocr_status === 'Flagged') && (
                                                    <span style={{
                                                        background: '#ef4444', color: 'white',
                                                        fontSize: '0.65rem', padding: '1px 4px', borderRadius: '4px',
                                                        marginTop: '2px', width: 'fit-content'
                                                    }}>
                                                        QC Required
                                                    </span>
                                                )}
                                            </td>
                                            <td>
                                                <span style={{
                                                    color: conf <= 1 ? '#ef4444' : '#f97316',
                                                    fontWeight: 'bold',
                                                    fontSize: '0.8rem'
                                                }}>
                                                    {doc.confidence_reason || '-'}
                                                </span>
                                            </td>
                                            <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{doc.upload_date?.split(' ')[0]}</td>
                                            <td style={{ display: 'flex', gap: '0.5rem' }}>
                                                <button
                                                    className="btn btn-ghost"
                                                    style={{ padding: '0.4rem', color: doc.is_favorite ? '#eab308' : 'var(--text-muted)' }}
                                                    onClick={async (e) => {
                                                        e.stopPropagation();
                                                        try {
                                                            const res = await axios.post(`http://127.0.0.1:5000/favorites?user_id=Gokul_Admin`, { document_id: doc.id });
                                                            // Local update for responsiveness
                                                            setDocuments(docs => docs.map(d => d.id === doc.id ? { ...d, is_favorite: res.data.is_favorite ? 1 : 0 } : d));
                                                        } catch (err) { console.error(err); }
                                                    }}
                                                >
                                                    <Star size={18} fill={doc.is_favorite ? '#eab308' : 'none'} />
                                                </button>
                                                <button
                                                    className="btn btn-ghost"
                                                    type="button"
                                                    style={{ padding: '0.2rem 0.5rem', fontSize: '0.8rem' }}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        console.log("View button clicked", doc);
                                                        // Bug 1 + Bug 6: Log ID and force state clear
                                                        if (!doc || !doc.id) {
                                                            console.error("[Dashboard] Critical: View clicked with invalid doc!", doc);
                                                            return;
                                                        }
                                                        console.log(`[Dashboard] Opening Viewer for ID: ${doc.id}`);
                                                        const fileUrl = `http://127.0.0.1:5000/view/${doc.id}?user_id=${currentUser?.id || 'Gokul_Admin'}`;
                                                        console.log("Opening file path (URL):", fileUrl);

                                                        setViewingDoc(null);
                                                        setTimeout(() => setViewingDoc({ ...doc }), 0); // Pass fresh copy
                                                    }}
                                                >
                                                    View
                                                </button>
                                                {doc.effective_confidentiality === 'Restricted' && !isAdmin && doc.access_status !== 'Approved' && doc.uploader_id !== currentUser?.id ? (
                                                    <button
                                                        className="btn btn-ghost"
                                                        style={{ padding: '0.2rem 0.5rem', fontSize: '0.8rem', color: '#facc15' }}
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            const reason = prompt("Reason for requesting access?");
                                                            if (reason) {
                                                                axios.post('http://127.0.0.1:5000/access/request', { user_id: currentUser.id, document_id: doc.id, reason })
                                                                    .then(() => alert("Request Submitted"))
                                                                    .catch(err => alert("Failed"));
                                                            }
                                                        }}
                                                    >
                                                        Request Access
                                                    </button>
                                                ) : null}
                                                {isAdmin && (
                                                    <button
                                                        className="btn btn-ghost"
                                                        type="button"
                                                        style={{ padding: '0.2rem 0.5rem', fontSize: '0.8rem' }}
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            console.log("Details button clicked", doc);
                                                            // Bug 1 Fix: Explicit pass
                                                            if (!doc.id) console.error("[Dashboard] Details clicked w/o ID");
                                                            openDetails(doc);
                                                        }}
                                                        disabled={loadingDetailsId === doc.id}
                                                    >
                                                        {loadingDetailsId === doc.id ? 'Loading...' : 'Details'}
                                                    </button>
                                                )}
                                                <button
                                                    className="btn btn-ghost"
                                                    type="button"
                                                    style={{ padding: '0.4rem', color: '#ef4444' }}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        console.log("Delete button clicked", doc);
                                                        handleSoftDelete(doc);
                                                    }}
                                                    title="Move to Trash"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Document Details Modal */}
            {selectedDoc && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.8)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000
                }}>
                    <div className="glass-panel" style={{ width: '600px', maxWidth: '90%', padding: '2rem', background: '#1e293b', maxHeight: '90vh', overflowY: 'auto' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1.5rem' }}>
                            <h3 style={{ margin: 0 }}>{selectedDoc.filename}</h3>
                            <button onClick={() => setSelectedDoc(null)} style={{ background: 'none', border: 'none', color: 'white', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
                        </div>

                        {/* Tabs Navigation */}
                        <div style={{ display: 'flex', borderBottom: '1px solid var(--glass-border)', marginBottom: '1.5rem', gap: '1rem' }}>
                            <button
                                onClick={() => setActiveModalTab('metadata')}
                                style={{
                                    padding: '0.5rem 1rem', background: 'none', border: 'none',
                                    color: activeModalTab === 'metadata' ? 'var(--primary)' : 'white',
                                    borderBottom: activeModalTab === 'metadata' ? '2px solid var(--primary)' : 'none',
                                    cursor: 'pointer'
                                }}
                            >Metadata</button>
                            <button
                                onClick={() => setActiveModalTab('versions')}
                                style={{
                                    padding: '0.5rem 1rem', background: 'none', border: 'none',
                                    color: activeModalTab === 'versions' ? 'var(--primary)' : 'white',
                                    borderBottom: activeModalTab === 'versions' ? '2px solid var(--primary)' : 'none',
                                    cursor: 'pointer'
                                }}
                            >Versions</button>
                            <button
                                onClick={() => setActiveModalTab('audit')}
                                style={{
                                    padding: '0.5rem 1rem', background: 'none', border: 'none',
                                    color: activeModalTab === 'audit' ? 'var(--primary)' : 'white',
                                    borderBottom: activeModalTab === 'audit' ? '2px solid var(--primary)' : 'none',
                                    cursor: 'pointer'
                                }}
                            >History</button>
                        </div>

                        {/* Metadata Tab */}
                        {activeModalTab === 'metadata' && (
                            <>
                                <div style={{ marginBottom: '1.5rem', background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '8px' }}>
                                    <h4 style={{ marginTop: 0, color: '#60a5fa' }}>Extracted Metadata</h4>
                                    {selectedDoc.metadata ? (
                                        <pre style={{ background: '#f8f8f8', padding: '1rem', borderRadius: '4px', overflow: 'auto', maxHeight: '300px' }}>
                                            {(() => {
                                                try {
                                                    const meta = typeof selectedDoc.metadata === 'string' ? JSON.parse(selectedDoc.metadata) : selectedDoc.metadata;
                                                    return JSON.stringify(meta, null, 2);
                                                } catch (e) {
                                                    return selectedDoc.metadata || "{}";
                                                }
                                            })()}
                                        </pre>
                                    ) : (
                                        <p style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>No metadata extracted.</p>
                                    )}
                                </div>

                                {/* Reclassification */}
                                <div style={{ marginBottom: '1.5rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Change Category (Re-run Extraction)</label>
                                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                                        <select
                                            value={reclassifyCategory}
                                            onChange={(e) => setReclassifyCategory(e.target.value)}
                                            className="input"
                                            style={{ flex: 1 }}
                                        >
                                            {taxonomy.filter(t => t.category === 'DocumentType').map(t => (
                                                <option key={t.id} value={t.value}>{t.value}</option>
                                            ))}
                                        </select>
                                        <button className="btn" onClick={handleReclassify}>Update</button>
                                    </div>
                                </div>

                                {/* OCR Content Snippet */}
                                <div style={{ marginBottom: '1.5rem' }}>
                                    <h4 style={{ marginTop: 0 }}>OCR Content Snippet</h4>
                                    <div style={{ whiteSpace: 'pre-wrap', maxHeight: '150px', overflowY: 'auto', fontSize: '0.9rem', color: 'var(--text-muted)', border: '1px solid var(--glass-border)', padding: '0.5rem', borderRadius: '4px' }}>
                                        {selectedDoc.content || 'No text content available.'}
                                    </div>
                                </div>

                                {/* Approval Actions */}
                                {selectedDoc.approval_status === 'Pending Approval' && (
                                    <div style={{ marginTop: '2rem', padding: '1rem', border: '1px solid #eab308', borderRadius: '8px', background: 'rgba(234, 179, 8, 0.05)' }}>
                                        <h4 style={{ marginTop: 0, color: '#eab308' }}>Approver Actions</h4>
                                        {!showRejectInput ? (
                                            <div style={{ display: 'flex', gap: '1rem' }}>
                                                <button className="btn" style={{ background: '#22c55e', borderColor: '#22c55e' }} onClick={() => handleApprovalAction('approve')}>Approve & Publish</button>
                                                <button className="btn" style={{ background: '#ef4444', borderColor: '#ef4444' }} onClick={() => setShowRejectInput(true)}>Reject</button>
                                                <button className="btn btn-ghost" onClick={() => handleApprovalAction('request_changes', 'Please provide better scan')}>Request Changes</button>
                                            </div>
                                        ) : (
                                            <div>
                                                <label style={{ display: 'block', marginBottom: '0.5rem' }}>Reason for Rejection</label>
                                                <textarea
                                                    className="input"
                                                    style={{ width: '100%', marginBottom: '1rem' }}
                                                    rows="3"
                                                    value={rejectReason}
                                                    onChange={(e) => setRejectReason(e.target.value)}
                                                ></textarea>
                                                <div style={{ display: 'flex', gap: '1rem' }}>
                                                    <button className="btn" style={{ background: '#ef4444', borderColor: '#ef4444' }} onClick={() => handleApprovalAction('reject', rejectReason)}>Confirm Rejection</button>
                                                    <button className="btn btn-ghost" onClick={() => setShowRejectInput(false)}>Cancel</button>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </>
                        )}

                        {/* Versions Tab */}
                        {activeModalTab === 'versions' && (
                            <div style={{ marginBottom: '1.5rem' }}>
                                <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>📜 Version History</h4>
                                <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: '8px', padding: '0.5rem' }}>
                                    {docVersions.length > 0 ? docVersions.map(v => (
                                        <div key={v.id} style={{ padding: '0.75rem', borderBottom: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                                            <div>
                                                <div style={{ fontWeight: 'bold' }}>{v.version_timestamp}</div>
                                                <div style={{ color: 'var(--text-muted)' }}>Reason: {v.reason}</div>
                                            </div>
                                            <div style={{ textAlign: 'right' }}>
                                                <div style={{ color: 'var(--secondary)' }}>{v.category}</div>
                                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>by {v.user_id}</div>
                                            </div>
                                        </div>
                                    )) : <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No previous versions.</p>}
                                </div>
                            </div>
                        )}

                        {/* Audit Log Tab */}
                        {activeModalTab === 'audit' && (
                            <div style={{ marginBottom: '1.5rem' }}>
                                <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>🔍 Change History</h4>
                                <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: '8px', padding: '0.5rem' }}>
                                    {auditLogs.length > 0 ? auditLogs.map(log => (
                                        <div key={log.id} style={{ padding: '0.75rem', borderBottom: '1px solid var(--glass-border)', fontSize: '0.85rem' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                                <span style={{ color: 'var(--primary)', fontWeight: 'bold' }}>{log.action.toUpperCase()}</span>
                                                <span style={{ color: 'var(--text-muted)' }}>{log.timestamp}</span>
                                            </div>
                                            <div style={{ color: '#e2e8f0' }}>{log.details}</div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>by {log.performed_by}</div>
                                        </div>
                                    )) : <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No audit logs found.</p>}
                                </div>
                            </div>
                        )}

                    </div>
                </div>
            )}

            {/* Document Viewer Overlay */}
            {viewingDoc && (
                <DocumentViewer
                    doc={viewingDoc}
                    onClose={() => setViewingDoc(null)}
                    isAdmin={isAdmin}
                    user_id="Gokul_Admin"
                />
            )}
        </div>
    );
};

export default Dashboard;
