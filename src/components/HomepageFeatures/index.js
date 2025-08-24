import clsx from 'clsx';
import styles from './styles.module.css';

const CardList = [
  {
    title: 'Easy to Use',
    image: '/img/card1.jpg',
    description: 'Nuestra plataforma fue diseñada para que cualquier estudiante pueda usarla sin complicaciones.',
    link: '/docs/intro',
  },
  {
    title: 'Focus on What Matters',
    image: '/img/card2.jpg',
    description: 'Enfocate en tus aprendizajes, nosotros nos ocupamos de la organización y soporte.',
    link: '/docs/intro',
  },
  {
    title: 'Powered by React',
    image: '/img/card3.jpg',
    description: 'Construido con React, lo que permite expandir la revista con facilidad y rapidez.',
    link: '/docs/intro',
  },
];

function Card({title, image, description, link}) {
  return (
    <div className={clsx('col col--4')}>
      <div className={styles.card}>
        <img src={image} alt={title} className={styles.cardImage} />
        <div className={styles.cardBody}>
          <h3>{title}</h3>
          <p>{description}</p>
          <a href={link} className={styles.cardButton}>Ver más</a>
        </div>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {CardList.map((props, idx) => (
            <Card key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
