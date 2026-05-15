import { useState, useEffect } from 'react';
import { FileCheck, Loader, CheckSquare, Square, Sparkles, Edit3 } from 'lucide-react';
import { getDocuments, generateDraft, submitEdit } from '../services/api';
import toast from 'react-hot-toast';

const DRAFT_TYPES = [
  { value: 'case_fact_summary', label: 'Case Fact Summary', description: 'Parties, claims, dates, damages' },
  { value: 'title_review_summary', label: 'Title Review Summary', description: 'Property, ownership, encumbrances' },
  { value: 'notice_summary', label: 'Notice Summary', description: 'Notice type, deadlines, obligations' },
  { value: 'document_checklist', label: 'Document Checklist', description: 'Present/missing document analysis' },
  { value: 'internal_memo', label: 'Internal Memo', description: 'Partner-facing memo with findings' },
];

export default function DraftGeneration() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [draftType, setDraftType] = useState('case_fact_summary');
  const [additionalContext, setAdditionalContext] = useState('');
  const [generating, setGenerating] = useState(false);
  const [draft, setDraft] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editedContent, setEditedContent] = useState('');

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const data = await getDocuments();
      setDocuments(data.filter(doc => doc.status === 'ready'));
    } catch (error) {
      toast.error('Failed to load documents');
    }
  };

  const toggleDocument = (docId) => {
    setSelectedDocs(prev =>
      prev.includes(docId)
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
    );
  };

  const handleGenerate = async () => {
    if (selectedDocs.length === 0) {
      toast.error('Please select at least one document');
      return;
    }

    setGenerating(true);
    const toastId = toast.loading('Generating draft...');

    try {
      const result = await generateDraft({
        document_ids: selectedDocs,
        draft_type: draftType,
        additional_context: additionalContext || undefined,
      });
      
      setDraft(result);
      setEditedContent(result.content);
      toast.success('Draft generated successfully!', { id: toastId });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate draft', { id: toastId });
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!draft || editedContent === draft.content) {
      setEditMode(false);
      return;
    }

    try {
      await submitEdit(draft.draft_id, {
        original_text: draft.content,
        edited_text: editedContent,
        section_label: 'Full Draft',
        operator_note: 'Manual edit via UI',
      });
      
      toast.success('Edit saved! System will learn from this.');
      setDraft({ ...draft, content: editedContent });
      setEditMode(false);
    } catch (error) {
      toast.error('Failed to save edit');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Generate Draft</h1>
        <p className="mt-1 text-gray-600">
          Create grounded legal drafts from your processed documents
        </p>
      </div>

      {!draft ? (
        <>
          {/* Document Selection */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              1. Select Documents
            </h2>
            
            {documents.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-600 mb-4">No documents available</p>
                <a href="/upload" className="btn-primary">Upload Document</a>
              </div>
            ) : (
              <div className="space-y-2">
                {documents.map((doc) => (
                  <div
                    key={doc.document_id}
                    onClick={() => toggleDocument(doc.document_id)}
                    className="flex items-center space-x-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                  >
                    {selectedDocs.includes(doc.document_id) ? (
                      <CheckSquare className="h-5 w-5 text-primary-600" />
                    ) : (
                      <Square className="h-5 w-5 text-gray-400" />
                    )}
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{doc.filename}</p>
                      <p className="text-sm text-gray-600">
                        {doc.page_count} pages • {doc.chunk_count} chunks
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Draft Type Selection */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              2. Choose Draft Type
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {DRAFT_TYPES.map((type) => (
                <div
                  key={type.value}
                  onClick={() => setDraftType(type.value)}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                    draftType === type.value
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <p className="font-medium text-gray-900">{type.label}</p>
                  <p className="text-sm text-gray-600 mt-1">{type.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Additional Context */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              3. Additional Context (Optional)
            </h2>
            
            <textarea
              value={additionalContext}
              onChange={(e) => setAdditionalContext(e.target.value)}
              placeholder="Add any specific instructions or context for the draft generation..."
              rows={4}
              className="input"
            />
          </div>

          {/* Generate Button */}
          <div className="flex justify-end">
            <button
              onClick={handleGenerate}
              disabled={generating || selectedDocs.length === 0}
              className="btn-primary flex items-center text-lg px-8 py-3"
            >
              {generating ? (
                <>
                  <Loader className="animate-spin h-5 w-5 mr-2" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="h-5 w-5 mr-2" />
                  Generate Draft
                </>
              )}
            </button>
          </div>
        </>
      ) : (
        <>
          {/* Draft Result */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Generated Draft</h2>
                <p className="text-sm text-gray-600">
                  Model: {draft.model_used} • Type: {draft.draft_type}
                </p>
              </div>
              <div className="flex space-x-2">
                {editMode ? (
                  <>
                    <button onClick={handleSaveEdit} className="btn-primary">
                      Save Edit
                    </button>
                    <button onClick={() => {
                      setEditMode(false);
                      setEditedContent(draft.content);
                    }} className="btn-secondary">
                      Cancel
                    </button>
                  </>
                ) : (
                  <>
                    <button onClick={() => setEditMode(true)} className="btn-secondary flex items-center">
                      <Edit3 className="h-4 w-4 mr-2" />
                      Edit
                    </button>
                    <button onClick={() => setDraft(null)} className="btn-secondary">
                      New Draft
                    </button>
                  </>
                )}
              </div>
            </div>

            {editMode ? (
              <textarea
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                rows={20}
                className="input font-mono text-sm"
              />
            ) : (
              <div className="bg-gray-50 rounded-lg p-6 prose max-w-none">
                <pre className="whitespace-pre-wrap font-sans text-sm text-gray-900">
                  {draft.content}
                </pre>
              </div>
            )}
          </div>

          {/* Evidence Used */}
          {draft.evidence && draft.evidence.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Evidence Used ({draft.evidence.length} chunks)
              </h3>
              <div className="space-y-3">
                {draft.evidence.slice(0, 5).map((ev, idx) => (
                  <div key={idx} className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-900">
                        {ev.source_filename} {ev.page_number && `(Page ${ev.page_number})`}
                      </span>
                      <span className="badge badge-info">
                        {(ev.relevance_score * 100).toFixed(0)}% relevant
                      </span>
                    </div>
                    <p className="text-sm text-gray-700">{ev.text_preview}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
