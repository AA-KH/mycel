import React, { useState, useEffect } from 'react';

interface DocumentViewerProps {
  url: string;
  fileType: 'pdf' | 'excel' | 'word' | 'ppt' | 'unknown';
  filename?: string;
}

interface PPTSlide {
  title: string;
  content: string;
  theme?: string;
}

interface PPTData {
  title: string;
  subtitle?: string;
  slides: PPTSlide[];
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({ url, fileType, filename }) => {
  const isPdf = fileType === 'pdf';
  const isPpt = fileType === 'ppt';
  
  const [pptData, setPptData] = useState<PPTData | null>(null);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [loadingPpt, setLoadingPpt] = useState(false);

  useEffect(() => {
    if (isPpt && url.endsWith('.json')) {
      setLoadingPpt(true);
      fetch(url)
        .then(res => res.json())
        .then(data => {
          setPptData(data);
          setLoadingPpt(false);
          setCurrentSlide(0);
        })
        .catch(err => {
          console.error("Failed to fetch PPT JSON", err);
          setLoadingPpt(false);
        });
    }
  }, [url, isPpt]);

  const handleNext = () => {
    if (pptData && currentSlide < pptData.slides.length - 1) {
      setCurrentSlide(s => s + 1);
    }
  };

  const handlePrev = () => {
    if (currentSlide > 0) {
      setCurrentSlide(s => s - 1);
    }
  };

  return (
    <div className="w-full h-full min-h-[500px] flex flex-col bg-white rounded-lg border shadow-sm">
      <div className="p-4 border-b flex justify-between items-center bg-gray-50">
        <div className="flex items-center gap-2">
          <span className="text-2xl">
            {isPdf ? '📄' : fileType === 'excel' ? '📊' : fileType === 'ppt' ? '📽️' : '📝'}
          </span>
          <span className="font-semibold text-gray-700">{filename || 'Document'}</span>
        </div>
        <a 
          href={url} 
          download 
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
        >
          Download
        </a>
      </div>
      
      <div className="flex-grow p-4 flex items-center justify-center bg-gray-100 relative">
        {isPdf ? (
          <iframe src={`${url}#toolbar=0`} className="w-full h-full min-h-[600px] rounded" title="PDF Viewer" />
        ) : isPpt && url.endsWith('.json') ? (
          loadingPpt ? (
            <div className="text-gray-500 font-medium flex items-center gap-2">
              <span className="animate-spin text-xl">⏳</span> Loading Presentation...
            </div>
          ) : pptData ? (
            <div className="w-full max-w-5xl aspect-video bg-gradient-to-br from-slate-900 to-indigo-950 rounded-xl shadow-2xl flex flex-col overflow-hidden text-white relative border border-white/10">
              {/* Slide Content */}
              <div className="flex-grow p-12 flex flex-col justify-center relative z-10">
                <h2 className="text-4xl md:text-5xl font-bold mb-8 text-indigo-100 leading-tight">
                  {pptData.slides[currentSlide]?.title || pptData.title}
                </h2>
                <div className="text-xl md:text-2xl text-slate-300 whitespace-pre-wrap leading-relaxed">
                  {pptData.slides[currentSlide]?.content || pptData.subtitle || ''}
                </div>
              </div>
              
              {/* Background Decoration */}
              <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 z-0 pointer-events-none transform translate-x-1/2 -translate-y-1/2" />
              <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 z-0 pointer-events-none transform -translate-x-1/3 translate-y-1/3" />
              
              {/* Slide Footer / Navigation */}
              <div className="h-16 bg-black/40 flex items-center justify-between px-6 border-t border-white/10 relative z-10">
                <span className="text-sm text-slate-400 font-medium truncate max-w-[30%]">
                  {pptData.title}
                </span>
                <div className="flex items-center gap-4">
                  <button 
                    onClick={handlePrev}
                    disabled={currentSlide === 0}
                    className="px-4 py-1.5 hover:bg-white/10 rounded-md disabled:opacity-30 disabled:hover:bg-transparent transition-all font-medium text-sm"
                  >
                    ← Prev
                  </button>
                  <span className="text-sm text-slate-300 font-medium w-16 text-center">
                    {currentSlide + 1} / {pptData.slides.length}
                  </span>
                  <button 
                    onClick={handleNext}
                    disabled={currentSlide === pptData.slides.length - 1}
                    className="px-4 py-1.5 hover:bg-white/10 rounded-md disabled:opacity-30 disabled:hover:bg-transparent transition-all font-medium text-sm"
                  >
                    Next →
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-red-500 bg-red-50 p-4 rounded-lg border border-red-200">
              Failed to load presentation. Please try downloading the file directly.
            </div>
          )
        ) : (
          <div className="text-center">
            <div className="text-6xl mb-4">⬇️</div>
            <h3 className="text-xl font-medium text-gray-800 mb-2">Preview not available</h3>
            <p className="text-gray-500 mb-4">This file type cannot be previewed in the browser.</p>
            <a href={url} download className="text-blue-600 hover:underline font-medium">
              Click here to download the file
            </a>
          </div>
        )}
      </div>
    </div>
  );
};
