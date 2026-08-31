import React from 'react';
import { VideoPlayer } from './Renderers/VideoPlayer';
import { DocumentViewer } from './Renderers/DocumentViewer';
import { CodePreview } from './Renderers/CodePreview';

export type OutputType = 'video' | 'pdf' | 'excel' | 'code' | 'text' | 'ppt';

export interface ProjectOutput {
  id: string;
  type: OutputType;
  title: string;
  url?: string;
  content?: string;
  metadata?: any;
}

interface ProjectWorkspaceProps {
  output: ProjectOutput | null;
}

export const ProjectWorkspace: React.FC<ProjectWorkspaceProps> = ({ output }) => {
  if (!output) {
    return (
      <div className="w-full h-full min-h-[400px] flex items-center justify-center bg-gray-50 border-2 border-dashed border-gray-300 rounded-xl">
        <div className="text-center text-gray-500">
          <span className="text-4xl block mb-2">🤖</span>
          <p>Agent workspace is ready.</p>
          <p className="text-sm">Submit a task to see the output here.</p>
        </div>
      </div>
    );
  }

  const renderOutput = () => {
    switch (output.type) {
      case 'video':
        return <VideoPlayer src={output.url!} title={output.title} />;
      case 'pdf':
      case 'excel':
      case 'ppt':
        return <DocumentViewer url={output.url!} fileType={output.type} filename={output.title} />;
      case 'code':
        return (
          <CodePreview 
            code={output.content!} 
            isWebProject={output.metadata?.isWebProject} 
            language={output.metadata?.language}
          />
        );
      case 'text':
      default:
        return (
          <div className="bg-white p-6 rounded-lg shadow-sm border whitespace-pre-wrap font-sans text-gray-800">
            <h2 className="text-2xl font-bold mb-4">{output.title}</h2>
            {output.content}
          </div>
        );
    }
  };

  return (
    <div className="w-full flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-800">Workspace Result</h2>
        <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium border border-green-200">
          Task Completed
        </span>
      </div>
      <div className="w-full bg-gray-100 p-2 rounded-xl border shadow-inner">
        {renderOutput()}
      </div>
    </div>
  );
};
