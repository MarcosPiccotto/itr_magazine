// src/components/VideoPlayer.jsx
import React from 'react';

export default function VideoPlayer({ src, width = 640, height = 360 }) {
    return (
        <div style={{ position: 'relative', paddingBottom: '56.25%', height: 0 }}>
            <iframe
                width={width}
                height={height}
                src={`https://www.youtube.com/embed/${src}`}
                title="YouTube video"
                style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}
                // frameBorder="0"
                allowFullScreen
            />
        </div>
    );
}


{/* <video
        src="/img/videos/mi-video.mp4"
        style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}
        controls
    /> */}