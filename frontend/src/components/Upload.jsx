import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { Upload as UploadIcon, X, FileText, Check, AlertCircle, Loader2 } from 'lucide-react';

const Upload = ({ onUploadSuccess, batchId = null, containerId = null }) => {
    const [files, setFiles] = useState([]);
    const [isUploading, setIsUploading] = useState(false);
    const [containers, setContainers] = useState([]);
    const [selectedContainer, setSelectedContainer] = useState(containerId || '');
    const [isFastTrack, setIsFastTrack] = useState(false);
    const [taxonomy, setTaxonomy] = useState([]);
    const [tags, setTags] = useState('');

    const [operator] = useState('Gokul_Admin');
    const [department] = useState('Finance');
    const [docType, setDocType] = useState('');
    const [selectedDepartment, setSelectedDepartment] = useState('Finance');
    const [docDate, setDocDate] = useState(new Date().toISOString().split('T')[0]);
    const [generalSuggestions, setGeneralSuggestions] = useState(null);

    useEffect(() => {
        const fetchTaxonomy = async () => {
            try {
                const res = await axios.get('http://localhost:5000/taxonomy');
                setTaxonomy(res.data.filter(t => t.status === 'Active'));
            } catch (err) { console.error(err); }
        };
        fetchTaxonomy();

        if (!containerId) {
            const fetchContainers = async () => {
                try {
                    const res = await axios.get('http://localhost:5000/containers');
                    setContainers(res.data);
                } catch (error) { console.error("Failed to load containers"); }
            };
            fetchContainers();
        }
    }, [containerId]);

    const onDrop = useCallback((acceptedFiles) => {
        const newFiles = acceptedFiles.map(file => ({
            file,
            id: Math.random().toString(36).substring(7),
            status: 'idle',
            progress: 0,
            result: null,
            error: null
        }));
        setFiles(prev => [...prev, ...newFiles]);
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'image/*': ['.jpeg', '.jpg', '.png'], 'application/pdf': ['.pdf'] }
    });

    const removeFile = (id) => {
        if (isUploading) return;
        setFiles(prev => prev.filter(f => f.id !== id));
    };

    const uploadFile = async (fileObj) => {
        const formData = new FormData();
        formData.append('file', fileObj.file);
        formData.append('tags', tags);
        formData.append('uploader_id', operator);

        if (containerId || selectedContainer) {
            formData.append('container_id', containerId || selectedContainer);
        }
        if (batchId) {
            formData.append('batch_id', batchId);
        }

        try {
            const response = await axios.post('http://localhost:5000/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                onUploadProgress: (progressEvent) => {
                    const progress = progressEvent.total
                        ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
                        : 0;
                    setFiles(prev => prev.map(f => f.id === fileObj.id ? { ...f, progress } : f));
                }
            });
            return { status: 'success', result: response.data };
        } catch (error) {
            return { status: 'error', error: error.response?.data?.error || 'Upload failed' };
        }
    };

    const handleUpload = async () => {
        setIsUploading(true);
        for (let i = 0; i < files.length; i++) {
            const fileObj = files[i];
            if (fileObj.status === 'success') continue;
            setFiles(prev => prev.map(f => f.id === fileObj.id ? { ...f, status: 'uploading' } : f));
            const result = await uploadFile(fileObj);
            if (result.status === 'success' && result.result.suggestions) {
                setGeneralSuggestions(result.result.suggestions);
            }
            setFiles(prev => prev.map(f => f.id === fileObj.id ? { ...f, status: result.status, result: result.result, error: result.error } : f));
            if (result.status === 'success' && onUploadSuccess) onUploadSuccess();
        }
        setIsUploading(false);
    };

    const hasFiles = files.length > 0;
    const allFinished = files.length > 0 && files.every(f => f.status === 'success' || f.status === 'error');

    return (
        <div className="glass-panel" style={{ padding: '2rem', marginBottom: '2rem' }}>
            <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <UploadIcon size={24} /> Upload Documents
            </h2>

            <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div className={`status-badge ${isFastTrack ? 'status-active' : ''}`} style={{ background: isFastTrack ? '#60a5fa' : '#475569' }}>
                        {isFastTrack ? 'Fast Track Active' : 'Standard Upload'}
                    </div>
                </div>
                <label className="switch" style={{ position: 'relative', display: 'inline-block', width: '50px', height: '26px' }}>
                    <input type="checkbox" checked={isFastTrack} onChange={() => setIsFastTrack(!isFastTrack)} />
                    <span className="slider round"></span>
                </label>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem', fontSize: '0.85rem' }}>
                <div style={{ color: 'var(--text-muted)' }}><strong>Operator:</strong> {operator}</div>
                <div>
                    <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.85rem' }}>Department</label>
                    <select className="input" value={selectedDepartment} onChange={e => setSelectedDepartment(e.target.value)} style={{ width: '100%' }}>
                        {taxonomy.filter(t => t.category === 'Department').map(t => <option key={t.id} value={t.value}>{t.value}</option>)}
                    </select>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                <div>
                    <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.85rem' }}>Document Type</label>
                    <select className="input" value={docType || (generalSuggestions?.category || '')} onChange={e => setDocType(e.target.value)} style={{ width: '100%' }}>
                        <option value="">Auto-Detect</option>
                        {taxonomy.filter(t => t.category === 'DocumentType').map(t => <option key={t.id} value={t.value}>{t.value}</option>)}
                    </select>
                </div>
                <div>
                    <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.85rem' }}>Tags (comma-separated)</label>
                    <input type="text" className="input" placeholder="e.g. urgent, q4" value={tags} onChange={e => setTags(e.target.value)} style={{ width: '100%' }} />
                </div>
            </div>

            {!containerId && (
                <div style={{ marginBottom: '1.5rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Assign to Container (Optional)</label>
                    <select value={selectedContainer} onChange={(e) => setSelectedContainer(e.target.value)} className="input" style={{ width: '100%' }}>
                        <option value="">-- Direct Upload (No Container) --</option>
                        {containers.map(c => <option key={c.id} value={c.id}>{c.id} - {c.department}</option>)}
                    </select>
                </div>
            )}

            <div {...getRootProps()} style={{ border: '2px dashed var(--glass-border)', borderRadius: '12px', padding: '3rem', textAlign: 'center', cursor: isUploading ? 'default' : 'pointer', background: isDragActive ? 'rgba(255, 255, 255, 0.05)' : 'transparent', opacity: isUploading ? 0.6 : 1 }}>
                <input {...getInputProps()} disabled={isUploading} />
                <p style={{ color: 'var(--text-muted)' }}>Drag & drop files here, or click to select</p>
            </div>

            {hasFiles && (
                <div style={{ marginTop: '2rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {files.map(f => (
                        <div key={f.id} style={{ background: 'rgba(255, 255, 255, 0.03)', borderRadius: '8px', padding: '1rem', display: 'flex', alignItems: 'center', gap: '1rem', border: '1px solid var(--glass-border)' }}>
                            <FileText size={20} style={{ color: 'var(--text-muted)' }} />
                            <div style={{ flex: 1 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ fontWeight: 500 }}>{f.file.name}</span>
                                    {f.status === 'success' && <Check size={18} color="#4ade80" />}
                                    {f.status === 'error' && <AlertCircle size={18} color="#f87171" />}
                                    {f.status === 'uploading' && <Loader2 size={18} className="spin" />}
                                </div>
                                {f.status === 'uploading' && <div style={{ height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', marginTop: '0.5rem' }}><div style={{ width: `${f.progress}%`, height: '100%', background: '#60a5fa' }} /></div>}
                            </div>
                            {f.status === 'idle' && !isUploading && <button onClick={() => removeFile(f.id)} style={{ background: 'none', border: 'none', color: '#f87171', cursor: 'pointer' }}><X size={18} /></button>}
                        </div>
                    ))}
                </div>
            )}

            {hasFiles && !allFinished && (
                <button className="btn" onClick={handleUpload} disabled={isUploading} style={{ marginTop: '1.5rem', width: '100%', background: '#3b82f6' }}>
                    {isUploading ? 'Uploading...' : 'Upload All Files'}
                </button>
            )}
        </div>
    );
};

export default Upload;
