import React, { useState } from 'react';

interface CodePreviewProps {
  code: string;
  language?: string;
  isWebProject?: boolean;
}

export const CodePreview: React.FC<CodePreviewProps> = ({ code, language = 'javascript', isWebProject = false }) => {
  const [view, setView] = useState<'code' | 'preview'>('code');

  // Simple iframe srcDoc trick for HTML preview
  const iframeSrcDoc = isWebProject ? code : '';

  return (
    <div className="w-full h-full flex flex-col bg-[#1e1e1e] rounded-lg overflow-hidden border border-gray-700">
      <div className="flex bg-[#2d2d2d] px-4 py-2 gap-2">
        <button 
          className={`px-3 py-1 rounded text-sm ${view === 'code' ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`}
          onClick={() => setView('code')}
        >
          Code
        </button>
        {isWebProject && (
          <button 
            className={`px-3 py-1 rounded text-sm ${view === 'preview' ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`}
            onClick={() => setView('preview')}
          >
            Live Preview
          </button>
        )}
      </div>
      
      <div className="flex-grow relative h-[600px] overflow-auto p-4">
        {view === 'code' ? (
          <pre className="text-sm font-mono text-green-400">
            <code>{code}</code>
          </pre>
        ) : (
          <iframe 
            srcDoc={iframeSrcDoc} 
            className="w-full h-full bg-white border-0 rounded"
            title="Live Preview"
            sandbox="allow-scripts"
          />
        )}
      </div>
    </div>
  );
};
