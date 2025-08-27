import clsx from 'clsx';
import styles from './styles.module.css';
import Translate from '@docusaurus/Translate';

const CardList = [
  {
    title: <Translate>Fácil de usar</Translate>,
    image: '/img/card1.jpg',
    description: <Translate>Nuestra plataforma fue diseñada para que cualquier estudiante pueda usarla sin complicaciones.</Translate>,
    link: '/docs/intro',
  },
  {
    title: <Translate>Concentrate en lo que importa</Translate>,
    image: '/img/card2.jpg',
    description: <Translate>Enfocate en tus aprendizajes, nosotros nos ocupamos de la organización y soporte.</Translate>,
    link: '/docs/intro',
  },
  {
    title: <Translate>Construido con React</Translate>,
    image: '/img/card3.jpg',
    description: <Translate>Utilizamos una plataforma robusta, lo que permite expandir la revista con facilidad y rapidez.</Translate>,
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
