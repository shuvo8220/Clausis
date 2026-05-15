import { useState } from 'react';
import { Upload, FileText, CheckCircle, XCircle, Loader, AlertCircle } from 'lucide-react';
import { uploadDocument } from '../services/api';
import toast from 'react-hot-toast';

export default function DocumentUpload() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setResult(null);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    const toastId = toast.loading('Processing document...');

    try {
      console.log('Uploading file:', file.name);
      const data = await uploadDocument(file);
      console.log('Upload response:', data);
      
      setResult(data);
      toast.success('Document processed successfully!', { id: toastId });
    } catch (err) {
      console.error('Upload error:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Upload failed';
      toast.error(errorMsg, { id: toastId });
    } finally {
      setUploading(false);
    }
  };

  const resetUpload = () => {
    setFile(null);
    setResult(null);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Upload Document</h1>
        <p className="mt-1 text-gray-600">
          Upload legal documents (PDF, TXT, or images) for processing and analysis
        </p>
      </div>

      {/* Upload Area */}
      {!result && (
        <div className="card">
          <div
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
              dragActive
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <Upload className={`mx-auto h-12 w-12 mb-4 ${dragActive ? 'text-primary-600' : 'text-gray-400'}`} />
            
            {!file ? (
              <>
                <p className="text-lg font-medium text-gray-900 mb-2">
                  Drop your file here, or click to browse
                </p>
                <p className="text-sm text-gray-500 mb-4">
                  Supports PDF, TXT, PNG, JPG, JPEG, TIFF (Max 50MB)
                </p>
                <label className="btn-primary cursor-pointer inline-block">
                  Choose File
                  <input
                    type="file"
                    className="hidden"
                    accept=".pdf,.txt,.png,.jpg,.jpeg,.tiff"
                    onChange={handleFileChange}
                  />
                </label>
              </>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-center text-gray-700">
                  <FileText className="h-5 w-5 mr-2 text-primary-600" />
                  <span className="font-medium">{file.name}</span>
                  <span className="ml-2 text-sm text-gray-500">
                    ({(file.size / 1024).toFixed(2)} KB)
                  </span>
                </div>
                
                <div className="flex items-center justify-center space-x-3">
                  <button
                    onClick={handleUpload}
                    disabled={uploading}
                    className="btn-primary flex items-center"
                  >
                    {uploading ? (
                      <>
                        <Loader className="animate-spin h-5 w-5 mr-2" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Upload className="h-5 w-5 mr-2" />
                        Upload & Process
                      </>
                    )}
                  </button>
                  
                  <button
                    onClick={resetUpload}
                    disabled={uploading}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Supported Features */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-start space-x-3">
              <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-gray-900 text-sm">OCR Support</p>
                <p className="text-xs text-gray-600">Automatic text extraction from scanned documents</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-gray-900 text-sm">Field Extraction</p>
                <p className="text-xs text-gray-600">Automatic extraction of dates, parties, amounts</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-gray-900 text-sm">Vector Indexing</p>
                <p className="text-xs text-gray-600">Semantic search ready for draft generation</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Success Result */}
      {result && (
        <div className="card border-green-200 bg-green-50">
          <div className="flex items-start">
            <CheckCircle className="h-6 w-6 text-green-600 mr-3 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-green-900 mb-4">
                Document Processed Successfully
              </h3>
              
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs font-medium text-gray-600">Filename</p>
                  <p className="text-sm text-gray-900 font-medium">{result.filename}</p>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs font-medium text-gray-600">Status</p>
                  <span className="badge badge-success">{result.status}</span>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs font-medium text-gray-600">Pages</p>
                  <p className="text-sm text-gray-900 font-medium">{result.page_count}</p>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs font-medium text-gray-600">Chunks Indexed</p>
                  <p className="text-sm text-gray-900 font-medium">{result.chunk_count}</p>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs font-medium text-gray-600">OCR Applied</p>
                  <p className="text-sm text-gray-900 font-medium">
                    {result.ocr_applied ? 'Yes' : 'No'}
                  </p>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs font-medium text-gray-600">Document ID</p>
                  <p className="text-xs text-gray-900 font-mono truncate">
                    {result.document_id}
                  </p>
                </div>
              </div>

              {result.structured_fields && Object.keys(result.structured_fields).length > 0 && (
                <div className="bg-white rounded-lg p-4 mb-4">
                  <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                    <AlertCircle className="h-4 w-4 mr-2 text-primary-600" />
                    Extracted Fields
                  </h4>
                  <div className="bg-gray-50 rounded p-3 text-xs font-mono overflow-x-auto">
                    <pre className="whitespace-pre-wrap">
                      {JSON.stringify(result.structured_fields, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {result.raw_text_preview && (
                <div className="bg-white rounded-lg p-4 mb-4">
                  <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                    <FileText className="h-4 w-4 mr-2 text-primary-600" />
                    Extracted Text Preview ({result.text_length} characters)
                  </h4>
                  <div className="bg-gray-50 rounded p-3 text-sm overflow-x-auto max-h-48 overflow-y-auto">
                    <pre className="whitespace-pre-wrap font-sans">
                      {result.raw_text_preview}
                      {result.text_length > 500 && <span className="text-gray-500">... (truncated)</span>}
                    </pre>
                  </div>
                </div>
              )}

              {result.processing_notes && result.processing_notes.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                  <h4 className="font-medium text-yellow-900 mb-2 flex items-center">
                    <AlertCircle className="h-4 w-4 mr-2" />
                    Processing Notes
                  </h4>
                  <ul className="list-disc list-inside text-sm text-yellow-800 space-y-1">
                    {result.processing_notes.map((note, idx) => (
                      <li key={idx}>{note}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex space-x-3">
                <button onClick={resetUpload} className="btn-primary">
                  Upload Another Document
                </button>
                <a href="/generate" className="btn-secondary">
                  Generate Draft
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
