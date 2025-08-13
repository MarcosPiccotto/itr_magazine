// src/components/ColorText.js
import React from 'react';

function ColorText({ color, children }) {
    // El estilo se aplica directamente al elemento <span>
    return (
        <span style={{ color: color }}>
            {children}
        </span>
    );
}

export default ColorText;