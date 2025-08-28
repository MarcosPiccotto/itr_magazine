import OriginalSidebarItem from '@theme-original/DocSidebarItem';
import { useLocation } from '@docusaurus/router';
import { Download } from "lucide-react";
import styles from './custom.css';

export default function DocSidebarItemWrapper(props) {
  const location = useLocation();

  const handlePrint = (e) => {
    e.stopPropagation(); // evita que navegue al link
    window.print();
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      {/* Render original sidebar link */}
      <OriginalSidebarItem {...props} />

      {/* Solo mostrar botón si es un documento */}
      {props.item.type === 'link' && props.item.docId && (
        <button
          onClick={handlePrint}
          title="Descargar"
          className="download-btn"
        >
          <Download size={16} />
        </button>
      )}
    </div>
  );
}
