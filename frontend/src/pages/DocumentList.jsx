import { useState, useEffect } from 'react';
import { FileText, Trash2, RefreshCw, Search, Calendar, FileCheck } from 'lucide-react';
import { getDocuments, deleteDocument } from '../services/api';
import toast from 'react-hot-toast';

export default function DocumentList() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [deleting, setDeleting] = useState(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const data = await getDocuments();
      setDocuments(data);
    } catch (error) {
      toast.error('Failed to load documents');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (docId, filename) => {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;

    setDeleting(docId);
    try {
      await deleteDocument(docId);
      setDocuments(documents.filter(doc => doc.document_id !== docId));
      toast.success('Document deleted successfully');
    } catch (error) {
      toast.error('Failed to delete document');
      console.error(error);
    } finally {
      setDeleting(null);
    }
  };

  const filteredDocuments = documents.filter(doc =>
    doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Documents</h1>
          <p className="mt-1 text-gray-600">
            Manage your uploaded and processed documents
          </p>
        </div>
        <button
          onClick={loadDocuments}
          disabled={loading}
          className="btn-secondary flex items-center"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Search */}
      <div className="card">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search documents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input pl-10"
          />
        </div>
      </div>

      {/* Documents List */}
      {loading ? (
        <div className="card text-center py-12">
          <RefreshCw className="h-8 w-8 text-gray-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading documents...</p>
        </div>
      ) : filteredDocuments.length === 0 ? (
        <div className="card text-center py-12">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {searchTerm ? 'No documents found' : 'No documents yet'}
          </h3>
          <p className="text-gray-600 mb-4">
            {searchTerm
              ? 'Try adjusting your search terms'
              : 'Upload your first document to get started'}
          </p>
          {!searchTerm && (
            <a href="/upload" className="btn-primary inline-block">
              Upload Document
            </a>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredDocuments.map((doc) => (
            <div key={doc.document_id} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4 flex-1">
                  <div className="p-3 bg-primary-100 rounded-lg">
                    <FileText className="h-6 w-6 text-primary-600" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-gray-900 truncate">
                      {doc.filename}
                    </h3>
                    
                    <div className="mt-2 flex flex-wrap gap-2">
                      <span className={`badge ${
                        doc.status === 'ready' ? 'badge-success' :
                        doc.status === 'failed' ? 'badge-danger' :
                        'badge-warning'
                      }`}>
                        {doc.status}
                      </span>
                      
                      {doc.ocr_applied && (
                        <span className="badge badge-info">OCR Applied</span>
                      )}
                    </div>
                    
                    <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-gray-600">Pages</p>
                        <p className="font-medium text-gray-900">{doc.page_count}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Chunks</p>
                        <p className="font-medium text-gray-900">{doc.chunk_count}</p>
                      </div>
                      <div className="col-span-2">
                        <p className="text-gray-600">Document ID</p>
                        <p className="font-mono text-xs text-gray-900 truncate">
                          {doc.document_id}
                        </p>
                      </div>
                    </div>

                    {doc.processing_notes && doc.processing_notes.length > 0 && (
                      <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded p-2">
                        <p className="text-xs font-medium text-yellow-900 mb-1">Notes:</p>
                        <ul className="text-xs text-yellow-800 space-y-1">
                          {doc.processing_notes.slice(0, 2).map((note, idx) => (
                            <li key={idx}>• {note}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>

                <button
                  onClick={() => handleDelete(doc.document_id, doc.filename)}
                  disabled={deleting === doc.document_id}
                  className="ml-4 p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                  title="Delete document"
                >
                  <Trash2 className="h-5 w-5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Stats */}
      {!loading && documents.length > 0 && (
        <div className="card bg-gray-50">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-6">
              <div>
                <span className="text-gray-600">Total Documents:</span>
                <span className="ml-2 font-semibold text-gray-900">{documents.length}</span>
              </div>
              <div>
                <span className="text-gray-600">Total Chunks:</span>
                <span className="ml-2 font-semibold text-gray-900">
                  {documents.reduce((sum, doc) => sum + (doc.chunk_count || 0), 0)}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
