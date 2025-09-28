import './App.css'
import datapizzaLogo from '../logos/datapizzaLogo.png'
import assolombardaLogo from '../logos/Asso.png'

function App() {
  return (
    <div className="page">
      <header className="brand-header">
        <figure className="brand-card datapizza">
          <img src={datapizzaLogo} alt="Logo Datapizza" />
          <figcaption>Creato dal team Datapizza</figcaption>
        </figure>
        <span className="brand-separator" aria-hidden="true">
          →
        </span>
        <figure className="brand-card assolombarda">
          <img src={assolombardaLogo} alt="Logo Assolombarda" />
          <figcaption>Per lo showcase Assolombarda</figcaption>
        </figure>
      </header>

      <main className="content">
        <h1>Lesson Showcase</h1>
        <p>
          Questo spazio raccoglie i materiali creati per presentare le lezioni
          dedicate ad Assolombarda. Il percorso nasce dalla collaborazione fra
          il team Datapizza e gli stakeholder Assolombarda, con l&apos;obiettivo di
          mettere in luce i risultati più interessanti e le prossime attività.
        </p>
        <p className="cta">
          Esplora i moduli per scoprire le demo, gli insight e le proposte di
          evoluzione realizzate per la community Assolombarda.
        </p>
      </main>
    </div>
  )
}

export default App
