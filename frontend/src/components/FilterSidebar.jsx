import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Filter, X, ChevronDown, ChevronRight, Star, Bookmark } from 'lucide-react';

const FilterSidebar = ({ onFilterChange, filters, isAdmin }) => {
    const [isOpen, setIsOpen] = useState(true);
    const [options, setOptions] = useState({
        subsidiaries: [],
        departments: [],
        functions: [],
        document_types: []
    });
    const [savedSearches, setSavedSearches] = useState([]);
    const [searchName, setSearchName] = useState('');
    const [showSaveInput, setShowSaveInput] = useState(false);

    useEffect(() => {
        const fetchOptions = async () => {
            try {
                const [res, sRes] = await Promise.all([
                    axios.get('http://localhost:5000/taxonomy/filters'),
                    axios.get('http://localhost:5000/saved-searches?user_id=Gokul_Admin')
                ]);
                setOptions(res.data);
                setSavedSearches(sRes.data);
            } catch (err) {
                console.error("Failed to fetch sidebar data", err);
            }
        };
        fetchOptions();
    }, []);

    const handleChange = (field, value) => {
        onFilterChange(field, value);
    };

    const handleSaveSearch = async () => {
        if (!searchName) return;
        try {
            await axios.post('http://localhost:5000/saved-searches?user_id=Gokul_Admin', {
                name: searchName,
                query_params: filters
            });
            setSearchName('');
            setShowSaveInput(false);
            // Refresh saved searches
            const res = await axios.get('http://localhost:5000/saved-searches?user_id=Gokul_Admin');
            setSavedSearches(res.data);
        } catch (err) {
            console.error("Failed to save search", err);
        }
    };

    const handlePublishSearch = async (id) => {
        try {
            await axios.post(`http://localhost:5000/saved-searches/publish/${id}`);
            // Refresh
            const res = await axios.get('http://localhost:5000/saved-searches?user_id=Gokul_Admin');
            setSavedSearches(res.data);
        } catch (err) {
            console.error("Failed to publish search", err);
        }
    };

    const sectionStyle = {
        marginBottom: '1.5rem',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        paddingBottom: '1rem'
    };

    const labelStyle = {
        display: 'block',
        fontSize: '0.75rem',
        color: 'var(--text-muted)',
        marginBottom: '0.5rem',
        textTransform: 'uppercase',
        letterSpacing: '0.05rem'
    };

    return (
        <div style={{
            width: isOpen ? '280px' : '50px',
            transition: 'width 0.3s ease',
            height: 'fit-content',
            minHeight: '400px',
            background: 'rgba(255,255,255,0.03)',
            borderRadius: '12px',
            border: '1px solid var(--glass-border)',
            padding: isOpen ? '1.5rem' : '0.5rem',
            position: 'relative',
            overflow: 'hidden'
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: isOpen ? '1.5rem' : '0' }}>
                {isOpen && <h3 style={{ margin: 0, fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Filter size={18} /> Filters</h3>}
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', padding: '5px' }}
                >
                    {isOpen ? <X size={18} /> : <Filter size={20} />}
                </button>
            </div>

            {isOpen && (
                <div className="animate-fade-in">
                    {/* Organization Section */}
                    <div style={sectionStyle}>
                        <label style={labelStyle}>Organization</label>
                        <select
                            className="input"
                            style={{ width: '100%', marginBottom: '0.5rem' }}
                            value={filters.subsidiary || ''}
                            onChange={(e) => handleChange('subsidiary', e.target.value)}
                        >
                            <option value="">All Subsidiaries</option>
                            {options.subsidiaries.map(s => <option key={s} value={s}>{s}</option>)}
                        </select>
                        <select
                            className="input"
                            style={{ width: '100%', marginBottom: '0.5rem' }}
                            value={filters.department || ''}
                            onChange={(e) => handleChange('department', e.target.value)}
                        >
                            <option value="">All Departments</option>
                            {options.departments.map(d => <option key={d} value={d}>{d}</option>)}
                        </select>
                        <select
                            className="input"
                            style={{ width: '100%' }}
                            value={filters.function || ''}
                            onChange={(e) => handleChange('function', e.target.value)}
                        >
                            <option value="">All Functions</option>
                            {options.functions.map(f => <option key={f} value={f}>{f}</option>)}
                        </select>
                    </div>

                    {/* Classification Section */}
                    <div style={sectionStyle}>
                        <label style={labelStyle}>Classification</label>
                        <select
                            className="input"
                            style={{ width: '100%', marginBottom: '0.5rem' }}
                            value={filters.category || ''}
                            onChange={(e) => handleChange('category', e.target.value)}
                        >
                            <option value="">All Doc Types</option>
                            {options.document_types.map(t => <option key={t} value={t}>{t}</option>)}
                        </select>
                    </div>

                    {/* Metadata Section */}
                    <div style={sectionStyle}>
                        <label style={labelStyle}>Date Range</label>
                        <input
                            type="date"
                            className="input"
                            style={{ width: '100%', marginBottom: '0.5rem', fontSize: '0.8rem' }}
                            value={filters.start_date || ''}
                            onChange={(e) => handleChange('start_date', e.target.value)}
                        />
                        <input
                            type="date"
                            className="input"
                            style={{ width: '100%', marginBottom: '0.5rem', fontSize: '0.8rem' }}
                            value={filters.end_date || ''}
                            onChange={(e) => handleChange('end_date', e.target.value)}
                        />

                        <label style={{ ...labelStyle, marginTop: '1rem' }}>Tags</label>
                        <input
                            type="text"
                            className="input"
                            placeholder="Search tags..."
                            style={{ width: '100%' }}
                            value={filters.tags || ''}
                            onChange={(e) => handleChange('tags', e.target.value)}
                        />
                    </div>

                    {/* Lifecycle Section */}
                    <div style={sectionStyle}>
                        <label style={labelStyle}>Status</label>
                        <select
                            className="input"
                            style={{ width: '100%' }}
                            value={filters.status || ''}
                            onChange={(e) => handleChange('status', e.target.value)}
                        >
                            <option value="">All Statuses</option>
                            <option value="Completed">Completed (OCR)</option>
                            <option value="Pending">Pending Approval</option>
                            <option value="Published">Published</option>
                            <option value="Failed">Failed</option>
                        </select>
                    </div>

                    {/* Saved Searches Section */}
                    <div style={{ ...sectionStyle, borderBottom: 'none' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                            <label style={labelStyle}>Saved Searches</label>
                            <button
                                onClick={() => setShowSaveInput(!showSaveInput)}
                                style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: '0.7rem' }}
                            >
                                {showSaveInput ? 'Cancel' : '+ Save'}
                            </button>
                        </div>

                        {showSaveInput && (
                            <div style={{ marginBottom: '1rem' }}>
                                <input
                                    type="text"
                                    className="input"
                                    placeholder="Search name..."
                                    style={{ width: '100%', fontSize: '0.8rem', marginBottom: '0.5rem' }}
                                    value={searchName}
                                    onChange={(e) => setSearchName(e.target.value)}
                                />
                                <button className="btn" style={{ width: '100%', fontSize: '0.8rem' }} onClick={handleSaveSearch}>Save Current</button>
                            </div>
                        )}

                        <div style={{ maxHeight: '150px', overflowY: 'auto' }}>
                            {savedSearches.map(s => (
                                <div key={s.id} style={{
                                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                    padding: '0.4rem', borderRadius: '4px', cursor: 'pointer',
                                    background: 'rgba(255,255,255,0.02)', marginBottom: '4px',
                                    fontSize: '0.8rem'
                                }}>
                                    <span onClick={() => onFilterChange('bulk', s.query_params)} style={{ flex: 1 }}>
                                        {s.name} {s.is_public === 1 && <span style={{ fontSize: '0.6rem', color: '#10b981' }}>(Public)</span>}
                                    </span>
                                    {isAdmin && s.is_public === 0 && (
                                        <button
                                            onClick={() => handlePublishSearch(s.id)}
                                            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                                            title="Publish to Team"
                                        >
                                            <ChevronRight size={14} />
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    <button
                        className="btn btn-ghost"
                        style={{ width: '100%', marginTop: '1rem', fontSize: '0.8rem' }}
                        onClick={() => {
                            onFilterChange('reset', null);
                        }}
                    >
                        Reset All Filters
                    </button>
                </div>
            )}
        </div>
    );
};

export default FilterSidebar;
