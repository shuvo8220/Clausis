import { useState, useEffect } from 'react';
import { FileText, FileCheck, TrendingUp, Activity, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { healthCheck, getDocuments, getPatterns } from '../services/api';
import toast from 'react-hot-toast';

export default function Dashboard() {
  const [stats, setStats] = useState({
    documents: 0,
    patterns: 0,
    status: 'checking...'
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [health, docs, patterns] = await Promise.all([
        healthCheck(),
        getDocuments(),
        getPatterns()
      ]);

      setStats({
        documents: docs.length || health.indexed_documents || 0,
        patterns: patterns.length || 0,
        status: health.status === 'ok' ? 'Online' : 'Offline'
      });
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      toast.error('Failed to load dashboard data');
      setStats(prev => ({ ...prev, status: 'Offline' }));
    } finally {
      setLoading(false);
    }
  };

  const features = [
    {
      title: 'Upload Documents',
      description: 'Upload PDF, TXT, or image files for processing with OCR support',
      icon: FileText,
      color: 'bg-blue-500',
      link: '/upload'
    },
    {
      title: 'Generate Drafts',
      description: 'Create grounded legal drafts from processed documents',
      icon: FileCheck,
      color: 'bg-green-500',
      link: '/generate'
    },
    {
      title: 'View Patterns',
      description: 'Explore learned patterns from operator edits',
      icon: TrendingUp,
      color: 'bg-purple-500',
      link: '/patterns'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-gray-600">
            Welcome to Legal AI Document Processing System
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`h-3 w-3 rounded-full ${stats.status === 'Online' ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
          <span className="text-sm font-medium text-gray-700">{stats.status}</span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Documents</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">
                {loading ? '...' : stats.documents}
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <FileText className="h-8 w-8 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Learned Patterns</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">
                {loading ? '...' : stats.patterns}
              </p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <TrendingUp className="h-8 w-8 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">System Status</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">
                {stats.status}
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <Activity className="h-8 w-8 text-green-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Features */}
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Link
                key={feature.title}
                to={feature.link}
                className="card hover:shadow-md transition-shadow group"
              >
                <div className={`inline-flex p-3 rounded-lg ${feature.color} mb-4`}>
                  <Icon className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-primary-600 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-gray-600 text-sm mb-4">
                  {feature.description}
                </p>
                <div className="flex items-center text-primary-600 text-sm font-medium group-hover:translate-x-1 transition-transform">
                  Get Started
                  <ArrowRight className="ml-2 h-4 w-4" />
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* How It Works */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">How It Works</h2>
        <div className="space-y-4">
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0 w-8 h-8 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center font-bold">
              1
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Upload Documents</h3>
              <p className="text-gray-600 text-sm">
                Upload legal documents in PDF, TXT, or image format. The system automatically extracts text using OCR when needed.
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0 w-8 h-8 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center font-bold">
              2
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Generate Drafts</h3>
              <p className="text-gray-600 text-sm">
                Select documents and choose a draft type. The AI generates grounded drafts with evidence citations.
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0 w-8 h-8 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center font-bold">
              3
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Edit & Improve</h3>
              <p className="text-gray-600 text-sm">
                Review and edit drafts. The system learns from your edits to improve future generations.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
