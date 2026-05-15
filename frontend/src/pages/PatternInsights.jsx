import { useState, useEffect } from 'react';
import { TrendingUp, RefreshCw, Sparkles, AlertCircle, CheckCircle } from 'lucide-react';
import { getPatterns, extractPatterns } from '../services/api';
import toast from 'react-hot-toast';

const DRAFT_TYPES = [
  { value: 'case_fact_summary', label: 'Case Fact Summary' },
  { value: 'title_review_summary', label: 'Title Review Summary' },
  { value: 'notice_summary', label: 'Notice Summary' },
  { value: 'document_checklist', label: 'Document Checklist' },
  { value: 'internal_memo', label: 'Internal Memo' },
];

export default function PatternInsights() {
  const [patterns, setPatterns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [selectedType, setSelectedType] = useState('case_fact_summary');
  const [groupedPatterns, setGroupedPatterns] = useState({});

  useEffect(() => {
    loadPatterns();
  }, []);

  useEffect(() => {
    // Group patterns by draft type
    const grouped = patterns.reduce((acc, pattern) => {
      const type = pattern.draft_type;
      if (!acc[type]) acc[type] = [];
      acc[type].push(pattern);
      return acc;
    }, {});
    setGroupedPatterns(grouped);
  }, [patterns]);

  const loadPatterns = async () => {
    setLoading(true);
    try {
      const data = await getPatterns();
      setPatterns(data);
    } catch (error) {
      toast.error('Failed to load patterns');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleExtractPatterns = async () => {
    setExtracting(true);
    const toastId = toast.loading('Extracting patterns from edits...');

    try {
      const result = await extractPatterns({
        draft_type: selectedType,
        min_edits: 2,
      });
      
      toast.success(`Extracted ${result.patterns_extracted} patterns!`, { id: toastId });
      await loadPatterns();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to extract patterns', { id: toastId });
    } finally {
      setExtracting(false);
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Pattern Insights</h1>
          <p className="mt-1 text-gray-600">
            Learned patterns from operator edits to improve future drafts
          </p>
        </div>
        <button
          onClick={loadPatterns}
          disabled={loading}
          className="btn-secondary flex items-center"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Extract New Patterns */}
      <div className="card bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
              <Sparkles className="h-5 w-5 mr-2 text-purple-600" />
              Extract New Patterns
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Analyze recent operator edits to discover new improvement patterns
            </p>
            
            <div className="flex items-center space-x-3">
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="input max-w-xs"
              >
                {DRAFT_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
              
              <button
                onClick={handleExtractPatterns}
                disabled={extracting}
                className="btn-primary flex items-center"
              >
                {extracting ? (
                  <>
                    <RefreshCw className="animate-spin h-4 w-4 mr-2" />
                    Extracting...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Extract Patterns
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Patterns</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">
                {patterns.length}
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
              <p className="text-sm font-medium text-gray-600">Draft Types</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">
                {Object.keys(groupedPatterns).length}
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <CheckCircle className="h-8 w-8 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Confidence</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">
                {patterns.length > 0
                  ? ((patterns.reduce((sum, p) => sum + p.confidence, 0) / patterns.length) * 100).toFixed(0) + '%'
                  : '0%'}
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <Sparkles className="h-8 w-8 text-green-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Patterns by Draft Type */}
      {loading ? (
        <div className="card text-center py-12">
          <RefreshCw className="h-8 w-8 text-gray-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading patterns...</p>
        </div>
      ) : patterns.length === 0 ? (
        <div className="card text-center py-12">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Patterns Yet</h3>
          <p className="text-gray-600 mb-4">
            Patterns will be extracted automatically after operator edits accumulate
          </p>
          <p className="text-sm text-gray-500">
            Generate drafts and edit them to start building patterns
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedPatterns).map(([draftType, typePatterns]) => (
            <div key={draftType} className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 capitalize">
                {draftType.replace(/_/g, ' ')} ({typePatterns.length} patterns)
              </h3>
              
              <div className="space-y-4">
                {typePatterns.map((pattern, idx) => (
                  <div key={pattern.pattern_id || idx} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{pattern.description}</p>
                      </div>
                      <span className={`badge ${getConfidenceColor(pattern.confidence)} ml-3`}>
                        {(pattern.confidence * 100).toFixed(0)}% confidence
                      </span>
                    </div>

                    {pattern.example_before && pattern.example_after && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
                        <div className="bg-red-50 border border-red-200 rounded p-3">
                          <p className="text-xs font-medium text-red-900 mb-2">Before:</p>
                          <p className="text-sm text-red-800">{pattern.example_before}</p>
                        </div>
                        <div className="bg-green-50 border border-green-200 rounded p-3">
                          <p className="text-xs font-medium text-green-900 mb-2">After:</p>
                          <p className="text-sm text-green-800">{pattern.example_after}</p>
                        </div>
                      </div>
                    )}

                    {pattern.created_at && (
                      <p className="text-xs text-gray-500 mt-2">
                        Created: {new Date(pattern.created_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
