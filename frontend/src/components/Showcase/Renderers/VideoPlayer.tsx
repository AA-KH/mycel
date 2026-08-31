import React from 'react';

interface VideoPlayerProps {
  src: string;
  title?: string;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({ src, title }) => {
  return (
    <div className="w-full h-full flex flex-col items-center justify-center bg-gray-900 rounded-lg overflow-hidden">
      {title && <h3 className="text-white text-lg font-semibold py-2 w-full text-center bg-gray-800">{title}</h3>}
      <video 
        controls 
        className="max-w-full max-h-[80vh] outline-none"
        src={src}
      >
        Your browser does not support the video tag.
      </video>
    </div>
  );
};
