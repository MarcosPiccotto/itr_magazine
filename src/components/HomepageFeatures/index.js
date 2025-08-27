import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import { usePluginData } from '@docusaurus/useGlobalData';
import styles from './styles.module.css'; // Asegúrate de tener un archivo de estilos o ajústalo

// --- Componente de Tarjeta Individual ---
function Card({ title, image, description, link }) {
    return (
        <div className={clsx('col col--4')}>
            <div className={styles.card}>
                {/* Usamos require() para que Docusaurus maneje la imagen */}
                {image ?
                <img src={require(`@site/static/img/${image}`).default}alt={title} className={styles.cardImage} />
                :
                <img src="/img/fondo_principal.png" alt={title} className={styles.cardImage} />
                }
                <div className={styles.cardBody}>
                    <h3>{title}</h3>
                    <p>{description}</p>
                    {/* Es mejor usar Link para la navegación interna */}
                    <Link to={link} className={styles.cardButton}>Ver más</Link>
                </div>
            </div>
        </div>
    );
}

// --- Componente Principal que Muestra las Tarjetas ---
export default function PublicationCards() {
    const latestDocs = usePluginData('docusaurus-plugin-docs-global-data');

    if (!latestDocs || latestDocs.length === 0) {
        return (
            <section style={{ textAlign: 'center', padding: '4rem 0' }}>
                <h2>Últimas Publicaciones</h2>
                <p>No se encontraron publicaciones recientes.</p>
            </section>
        );
    }

    return (
        <section className={styles.features}>
            <div className="container">
                <div className="row">
                    {latestDocs.map((doc) => {
                        console.log(doc)
                        return <Card
                            key={doc.permalink}
                            title={doc.title}
                            description={doc.description}
                            image={doc.image}
                            link={doc.permalink}
                        />
                    }
                    )}
                </div>
            </div>
        </section>
    );
}