import React, { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

const AnalyticsView = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const res = await fetch('http://localhost:5000/analytics');
                const data = await res.json();
                setStats(data);
            } catch (err) {
                console.error("Failed to fetch analytics", err);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    if (loading) return <div className="glass-panel" style={{ padding: '2rem' }}>Loading Analytics...</div>;
    if (!stats) return <div className="glass-panel" style={{ padding: '2rem' }}>Failed to load data.</div>;

    // Transform data for Recharts
    const categoryData = Object.entries(stats.by_category || {}).map(([name, value]) => ({ name, value }));
    const statusData = Object.entries(stats.by_status || {}).map(([name, value]) => ({ name, value }));
    const throughputData = stats.daily_throughput || [];

    const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {/* KPI Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'center' }}>
                    <h3 style={{ margin: 0, fontSize: '2rem', color: '#60a5fa' }}>{stats.total_documents}</h3>
                    <p style={{ margin: '0.5rem 0 0', color: 'var(--text-muted)' }}>Total Documents</p>
                </div>
                <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'center' }}>
                    <h3 style={{ margin: 0, fontSize: '2rem', color: '#4ade80' }}>
                        {statusData.find(d => d.name === 'Completed')?.value || 0}
                    </h3>
                    <p style={{ margin: '0.5rem 0 0', color: 'var(--text-muted)' }}>Completed</p>
                </div>
                <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'center' }}>
                    <h3 style={{ margin: 0, fontSize: '2rem', color: '#f87171' }}>
                        {statusData.find(d => d.name === 'Failed')?.value || 0}
                    </h3>
                    <p style={{ margin: '0.5rem 0 0', color: 'var(--text-muted)' }}>Failed / Pending</p>
                </div>
            </div>

            {/* Charts Area */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '2rem' }}>

                {/* Category Distribution */}
                <div className="glass-panel" style={{ padding: '1.5rem', height: '400px' }}>
                    <h3 style={{ marginBottom: '1rem' }}>Document Categories</h3>
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={categoryData}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                outerRadius={120}
                                fill="#8884d8"
                                dataKey="value"
                            >
                                {categoryData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none' }} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                {/* Status Bar Chart */}
                <div className="glass-panel" style={{ padding: '1.5rem', height: '400px' }}>
                    <h3 style={{ marginBottom: '1rem' }}>Processing Status</h3>
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={statusData}>
                            <XAxis dataKey="name" stroke="var(--text-muted)" />
                            <YAxis stroke="var(--text-muted)" />
                            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none' }} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                            <Bar dataKey="value" fill="#82ca9d" radius={[4, 4, 0, 0]}>
                                {statusData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.name === 'Failed' ? '#f87171' : entry.name === 'Completed' ? '#4ade80' : '#60a5fa'} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Daily Throughput Line Chart */}
                <div className="glass-panel" style={{ padding: '1.5rem', height: '400px', gridColumn: '1 / -1' }}>
                    <h3 style={{ marginBottom: '1rem' }}>Daily Throughput (Last 7 Days)</h3>
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={throughputData}>
                            <XAxis dataKey="date" stroke="var(--text-muted)" />
                            <YAxis stroke="var(--text-muted)" />
                            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none' }} />
                            <Legend />
                            <Line type="monotone" dataKey="count" stroke="#8884d8" strokeWidth={3} dot={{ r: 6 }} activeDot={{ r: 8 }} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default AnalyticsView;
