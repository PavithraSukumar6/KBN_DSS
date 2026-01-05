import React, { useState } from 'react';
import DigitizationPipeline from './components/DigitizationPipeline';
import Dashboard from './components/Dashboard';
import IntakeForm from './components/IntakeForm';
import ContainerManager from './components/ContainerManager';
import QCQueue from './components/QCQueue';
import AnalyticsView from './components/AnalyticsView';
import GovernanceDashboard from './components/GovernanceDashboard';
import { LayoutDashboard, Box, ScanLine, Microscope, BarChart3, Shield, User, UserCheck } from 'lucide-react';

function App() {
    const [refreshKey, setRefreshKey] = useState(0);
    const [activeTab, setActiveTab] = useState('pipeline');
    const [globalSearch, setGlobalSearch] = useState('');
    const [isAdmin, setIsAdmin] = useState(false);

    const handleUploadSuccess = () => {
        setRefreshKey(prev => prev + 1);
    };

    const handleGlobalSearch = (e) => {
        if (e.key === 'Enter') {
            setActiveTab('pipeline'); // Go to library view
            setRefreshKey(prev => prev + 1);
        }
    };

    return (
        <div className="container">
            <header style={{
                textAlign: 'center',
                padding: '2rem 0',
                marginBottom: '1rem',
                position: 'relative'
            }}>
                <div style={{ position: 'absolute', top: '20px', right: '20px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <button
                        onClick={() => setIsAdmin(!isAdmin)}
                        className="btn btn-ghost"
                        style={{ background: isAdmin ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                    >
                        {isAdmin ? <UserCheck size={18} color="#60a5fa" /> : <User size={18} />}
                        {isAdmin ? "Admin Role" : "General User"}
                    </button>
                </div>
                <h1>🚀 Document Sorting & Digitization System</h1>
                <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem', marginBottom: '1.5rem' }}>
                    Physical Intake • Digitization • Classification • Archival
                </p>
                <div style={{ display: 'flex', justifyContent: 'center' }}>
                    <div style={{ position: 'relative' }}>
                        <input
                            type="text"
                            placeholder="Global Search Documents..."
                            value={globalSearch}
                            onChange={(e) => setGlobalSearch(e.target.value)}
                            onKeyDown={handleGlobalSearch}
                            style={{ padding: '0.65rem 1rem 0.65rem 2.5rem', borderRadius: '25px', width: '350px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'white' }}
                        />
                        <LayoutDashboard size={18} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
                    </div>
                </div>
            </header>

            {/* Navigation Tabs */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
                <button
                    onClick={() => setActiveTab('intake')}
                    className={`btn ${activeTab === 'intake' ? '' : 'btn-ghost'} `}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'intake' ? '#3b82f6' : 'transparent' }}
                >
                    <Box size={20} /> Container Intake
                </button>
                <button
                    onClick={() => setActiveTab('pipeline')}
                    className={`btn ${activeTab === 'pipeline' ? '' : 'btn-ghost'} `}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'pipeline' ? '#3b82f6' : 'transparent' }}
                >
                    <ScanLine size={20} /> Digitization Pipeline
                </button>
                <button
                    onClick={() => setActiveTab('qc')}
                    className={`btn ${activeTab === 'qc' ? '' : 'btn-ghost'} `}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'qc' ? '#3b82f6' : 'transparent' }}
                >
                    <Microscope size={20} /> QC Queue
                </button>
                <button
                    onClick={() => setActiveTab('analytics')}
                    className={`btn ${activeTab === 'analytics' ? '' : 'btn-ghost'} `}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'analytics' ? '#3b82f6' : 'transparent' }}
                >
                    <BarChart3 size={20} /> Analytics
                </button>
                <button
                    onClick={() => setActiveTab('governance')}
                    className={`btn ${activeTab === 'governance' ? '' : 'btn-ghost'} `}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'governance' ? '#3b82f6' : 'transparent' }}
                >
                    <Shield size={20} /> Governance
                </button>
            </div>

            <main>
                {activeTab === 'intake' ? (
                    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(350px, 1fr) 1fr', gap: '2rem' }}>
                        <IntakeForm onSuccess={() => setRefreshKey(prev => prev + 1)} />
                        <ContainerManager refreshTrigger={refreshKey} />
                    </div>
                ) : activeTab === 'qc' ? (
                    <QCQueue />
                ) : activeTab === 'analytics' ? (
                    <AnalyticsView />
                ) : activeTab === 'governance' ? (
                    <GovernanceDashboard />
                ) : (
                    <>
                        <DigitizationPipeline onUploadSuccess={handleUploadSuccess} />
                        <Dashboard refreshTrigger={refreshKey} globalSearch={globalSearch} isAdmin={isAdmin} />
                    </>
                )}
            </main>

            <footer style={{
                textAlign: 'center',
                padding: '2rem',
                color: 'var(--text-muted)',
                marginTop: '3rem',
                borderTop: '1px solid var(--glass-border)'
            }}>
                <p>Built with Flask + React • 2024</p>
            </footer>
        </div>
    );
}

export default App;
