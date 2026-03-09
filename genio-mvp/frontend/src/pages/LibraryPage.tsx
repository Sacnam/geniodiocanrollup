import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  FileText, 
  Upload, 
  Search, 
  Trash2, 
  Loader2, 
  File,
  Folder,
  BookOpen,
  GitBranch,
  Sparkles,
  Grid3X3,
  List,
  X,
  ExternalLink
} from 'lucide-react';
import { useDocuments, useUploadDocument, useDeleteDocument } from '../hooks/useDocuments';
import { Document } from '../services/documents';
import { AugmentedReader } from '../components/library/AugmentedReader';
import { ConceptMap } from '../components/library/ConceptMap';
import { GraphRAGSearch } from '../components/library/GraphRAGSearch';
import { PKGNode } from '../services/library';

type ViewMode = 'list' | 'grid' | 'reader' | 'concept-map' | 'search';

const getStatusColor = (status: string) => {
  switch (status) {
    case 'ready': return 'bg-green-100 text-green-700';
    case 'processing':
    case 'extracting':
    case 'indexing': return 'bg-yellow-100 text-yellow-700';
    case 'error': return 'bg-red-100 text-red-700';
    default: return 'bg-gray-100 text-gray-700';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'ready': return <FileText className="w-5 h-5 text-green-600" />;
    case 'processing':
    case 'extracting':
    case 'indexing': return <Loader2 className="w-5 h-5 text-yellow-600 animate-spin" />;
    case 'error': return <FileText className="w-5 h-5 text-red-600" />;
    default: return <FileText className="w-5 h-5 text-gray-600" />;
  }
};

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const LibraryPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [showReader, setShowReader] = useState(false);
  const [selectedNode, setSelectedNode] = useState<PKGNode | null>(null);
  
  const { data: documents, isLoading } = useDocuments({ search: searchQuery });
  const uploadMutation = useUploadDocument();
  const deleteMutation = useDeleteDocument();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach(file => {
      uploadMutation.mutate(file);
    });
  }, [uploadMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/epub+zip': ['.epub'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'text/html': ['.html', '.htm'],
    },
    maxSize: 50 * 1024 * 1024,
  });

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this document?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleOpenReader = (doc: Document) => {
    setSelectedDoc(doc);
    setShowReader(true);
  };

  const handleNodeSelect = (node: PKGNode) => {
    setSelectedNode(node);
    // Could open a node detail panel or navigate to related documents
  };

  // Render different views based on viewMode
  const renderContent = () => {
    switch (viewMode) {
      case 'concept-map':
        return (
          <div className="h-[calc(100vh-200px)]">
            <ConceptMap onNodeSelect={handleNodeSelect} height={600} />
          </div>
        );
      
      case 'search':
        return <GraphRAGSearch />;
      
      case 'reader':
        if (!selectedDoc) {
          return (
            <div className="text-center py-12">
              <BookOpen className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">Select a document to read</p>
            </div>
          );
        }
        return null; // Reader is shown in modal
      
      case 'grid':
        return (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {documents?.items.map((doc) => (
              <div
                key={doc.id}
                className="bg-white rounded-lg shadow border p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => handleOpenReader(doc)}
              >
                <div className="flex items-start justify-between mb-3">
                  {getStatusIcon(doc.status)}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(doc.id);
                    }}
                    className="text-red-400 hover:text-red-600"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <h3 className="font-medium text-gray-900 line-clamp-2 mb-2">
                  {doc.title || doc.original_filename}
                </h3>
                <p className="text-sm text-gray-500">
                  {doc.word_count?.toLocaleString() || 0} words
                </p>
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium mt-2 ${getStatusColor(doc.status)}`}>
                  {doc.status}
                </span>
              </div>
            ))}
          </div>
        );
      
      default: // list
        return (
          <div className="grid grid-cols-12 gap-6">
            {/* Document List */}
            <div className="col-span-12 lg:col-span-4">
              <div className="bg-white rounded-lg shadow border">
                <div className="p-4 border-b">
                  <h2 className="font-semibold">
                    Documents ({documents?.total || 0})
                  </h2>
                </div>
                
                <div className="divide-y max-h-[600px] overflow-y-auto">
                  {isLoading ? (
                    <div className="p-8 text-center">
                      <Loader2 className="w-8 h-8 animate-spin mx-auto text-gray-400" />
                    </div>
                  ) : documents?.items.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">
                      <File className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                      <p>No documents yet</p>
                      <p className="text-sm">Upload your first document above</p>
                    </div>
                  ) : (
                    documents?.items.map((doc) => (
                      <div
                        key={doc.id}
                        onClick={() => setSelectedDoc(doc)}
                        className={`
                          p-4 cursor-pointer hover:bg-gray-50 transition-colors
                          ${selectedDoc?.id === doc.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''}
                        `}
                      >
                        <div className="flex items-start gap-3">
                          {getStatusIcon(doc.status)}
                          <div className="flex-1 min-w-0">
                            <h3 className="font-medium text-gray-900 truncate">
                              {doc.title || doc.original_filename}
                            </h3>
                            <p className="text-sm text-gray-500">
                              {doc.word_count?.toLocaleString() || 0} words
                              {' · '}
                              {new Date(doc.created_at).toLocaleDateString()}
                            </p>
                            <span className={`
                              inline-flex items-center px-2 py-0.5 rounded text-xs font-medium mt-2
                              ${getStatusColor(doc.status)}
                            `}>
                              {doc.status}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Document Preview */}
            <div className="col-span-12 lg:col-span-8">
              {selectedDoc ? (
                <div className="bg-white rounded-lg shadow border">
                  <div className="p-4 border-b flex items-center justify-between">
                    <div>
                      <h2 className="font-semibold text-lg">
                        {selectedDoc.title || selectedDoc.original_filename}
                      </h2>
                      <p className="text-sm text-gray-500">
                        {selectedDoc.doc_type.toUpperCase()}
                        {selectedDoc.page_count && ` · ${selectedDoc.page_count} pages`}
                        {selectedDoc.word_count && ` · ${selectedDoc.word_count.toLocaleString()} words`}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {selectedDoc.status === 'ready' && (
                        <button
                          onClick={() => handleOpenReader(selectedDoc)}
                          className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          <BookOpen className="w-4 h-4" />
                          <span>Read</span>
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(selectedDoc.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>

                  <div className="p-6">
                    {selectedDoc.status === 'ready' ? (
                      <div className="prose max-w-none">
                        {selectedDoc.excerpt ? (
                          <>
                            <h3 className="text-lg font-medium mb-2">Preview</h3>
                            <p className="text-gray-700 whitespace-pre-wrap">
                              {selectedDoc.excerpt}...
                            </p>
                            <button 
                              onClick={() => handleOpenReader(selectedDoc)}
                              className="mt-4 text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
                            >
                              Read full document
                              <ExternalLink className="w-4 h-4" />
                            </button>
                          </>
                        ) : (
                          <p className="text-gray-500 italic">No preview available</p>
                        )}
                      </div>
                    ) : selectedDoc.status === 'error' ? (
                      <div className="text-center py-8">
                        <p className="text-red-600">Error processing document</p>
                        <p className="text-sm text-gray-500 mt-2">
                          Please try uploading again
                        </p>
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-600 mb-4" />
                        <p className="text-gray-600">Processing document...</p>
                        <p className="text-sm text-gray-500 mt-2">
                          Extracting text and generating embeddings
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="bg-white rounded-lg shadow border p-12 text-center">
                  <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Select a document
                  </h3>
                  <p className="text-gray-500">
                    Click on a document from the list to view details
                  </p>
                </div>
              )}
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Folder className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold">Library</h1>
            </div>
            
            <div className="flex items-center gap-4">
              {/* Search */}
              {viewMode !== 'search' && (
                <div className="relative">
                  <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Search documents..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 pr-4 py-2 border rounded-lg w-64 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              )}

              {/* View Mode Toggle */}
              <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded ${viewMode === 'list' ? 'bg-white shadow' : 'hover:bg-gray-200'}`}
                  title="List View"
                >
                  <List className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 rounded ${viewMode === 'grid' ? 'bg-white shadow' : 'hover:bg-gray-200'}`}
                  title="Grid View"
                >
                  <Grid3X3 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('concept-map')}
                  className={`p-2 rounded ${viewMode === 'concept-map' ? 'bg-white shadow' : 'hover:bg-gray-200'}`}
                  title="Concept Map"
                >
                  <GitBranch className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('search')}
                  className={`p-2 rounded ${viewMode === 'search' ? 'bg-white shadow' : 'hover:bg-gray-200'}`}
                  title="Knowledge Search"
                >
                  <Sparkles className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Upload Area - only show in list/grid modes */}
        {(viewMode === 'list' || viewMode === 'grid') && (
          <div className="mb-6">
            <div
              {...getRootProps()}
              className={`
                border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
                ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
              `}
            >
              <input {...getInputProps()} />
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              {isDragActive ? (
                <p className="text-lg text-blue-600">Drop files here...</p>
              ) : (
                <>
                  <p className="text-lg text-gray-700 mb-2">
                    Drag & drop files here, or click to select
                  </p>
                  <p className="text-sm text-gray-500">
                    Supports PDF, EPUB, DOCX, TXT, Markdown, HTML (max 50MB)
                  </p>
                </>
              )}
            </div>
          </div>
        )}

        {/* Content */}
        {renderContent()}
      </div>

      {/* Augmented Reader Modal */}
      {showReader && selectedDoc && (
        <AugmentedReader
          documentId={selectedDoc.id}
          title={selectedDoc.title || selectedDoc.original_filename}
          content={selectedDoc.content || selectedDoc.excerpt || ''}
          onClose={() => setShowReader(false)}
        />
      )}
    </div>
  );
};
