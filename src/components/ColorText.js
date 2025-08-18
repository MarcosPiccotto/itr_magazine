// src/components/ColorText.js
import React from 'react';
import { useColorMode } from '@docusaurus/theme-common';

function invertColor(hex) {
    // Limpia #
    hex = hex.replace(/^#/, '');
    if (hex.length === 3) {
        hex = hex.split('').map(c => c + c).join('');
    }
    const r = (255 - parseInt(hex.substr(0, 2), 16)).toString(16).padStart(2, '0');
    const g = (255 - parseInt(hex.substr(2, 2), 16)).toString(16).padStart(2, '0');
    const b = (255 - parseInt(hex.substr(4, 2), 16)).toString(16).padStart(2, '0');
    return `#${r}${g}${b}`;
}

function ColorText({ color = "#000000", children }) {
    const { colorMode } = useColorMode();

    // Si está en dark, calculo el inverso del color
    const appliedColor = colorMode === 'dark' ? invertColor(color) : color;

    return (
        <span style={{ color: appliedColor }}>
            {children}
        </span>
    );
}

export default ColorText;
