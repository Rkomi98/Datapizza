import React, { useState } from 'react';
import { Download, BookOpen, FileText, Table, Users, GitCompare, FileCheck, Workflow, MessageSquare, Sparkles } from 'lucide-react';
import datapizzaLogo from './assets/datapizza.png';
import ExerciseTimer from './ExerciseTimer.jsx';

const EserciziDataPizza = () => {
  const [activeTab, setActiveTab] = useState(0);

  const exercises = [
    {
      id: '01',
      title: 'Brainstorming',
      icon: BookOpen,
      color: 'from-pink-500 to-rose-500',
      bgColor: 'bg-pink-50',
      borderColor: 'border-pink-300',
      description: 'Sessione di brainstorming guidata per generare idee creative.',
      files: [
        { name: 'Istruzioni.docx', path: 'Esercizi/01_Brainstorming/Istruzioni.docx' },
        { name: 'Scheda tema esercizio.docx', path: 'Esercizi/01_Brainstorming/Scheda tema esercizio.docx' },
        { name: '[SPOILER] Prompt di supporto.docx', path: 'Esercizi/01_Brainstorming/[SPOILER - ALERT] Prompt di supporto.docx', spoiler: true }
      ]
    },
    {
      id: '02',
      title: 'Analisi Dati Excel',
      icon: Table,
      color: 'from-green-500 to-emerald-500',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-300',
      description: 'Analisi dei dati di produzione utilizzando Excel.',
      files: [
        { name: 'Istruzioni_Ottobre_2025_GSK.docx', path: 'Esercizi/02_Analisi_dati_Excel/Istruzioni_Ottobre_2025_GSK.docx' },
        { name: 'Analisi_dati_produzione_GSK_Ottobre2025.xlsx', path: 'Esercizi/02_Analisi_dati_Excel/Analisi_dati_produzione_GSK_Ottobre2025.xlsx' },
        { name: 'Appunti_del_manager_Ottobre_2025_aggiornati.docx', path: 'Esercizi/02_Analisi_dati_Excel/Appunti_del_manager_Ottobre_2025_aggiornati.docx' },
        { name: '[SPOILER] Prompt di supporto.docx', path: 'Esercizi/02_Analisi_dati_Excel/[SPOILER] - Prompt di supporto.docx', spoiler: true }
      ]
    },
    {
      id: '03',
      title: 'Confronto Documenti',
      icon: GitCompare,
      color: 'from-blue-500 to-cyan-500',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-300',
      description: 'Confronta e analizza le differenze tra documenti di training.',
      files: [
        { name: 'Istruzioni.docx', path: 'Esercizi/03_Confronto_documenti/Istruzioni.docx' },
        { name: '9000053590-49 Training e qualifica del personale.docx', path: 'Esercizi/03_Confronto_documenti/9000053590-49Training e qualifica del personale.docx' },
        { name: '9000053590-50 Training e qualifica del personale.docx', path: 'Esercizi/03_Confronto_documenti/9000053590-50 Training e qualifica del personale.docx' },
        { name: '[SPOILER] Prompt di supporto.docx', path: 'Esercizi/03_Confronto_documenti/[Spoiler] Prompt di supporto.docx', spoiler: true }
      ]
    },
    {
      id: '04',
      title: 'Meeting Minutes',
      icon: FileText,
      color: 'from-purple-500 to-violet-500',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-300',
      description: 'Sintetizza le minute di un meeting in modo strutturato.',
      files: [
        { name: 'Istruzioni.docx', path: 'Esercizi/04_Minute/Istruzioni.docx' },
        { name: 'Materiale - Meeting Minutes Synthesizer.docx', path: 'Esercizi/04_Minute/Materiale – Meeting‑Minutes Synthesizer.docx' },
        { name: '[SPOILER] Prompt di supporto.docx', path: 'Esercizi/04_Minute/[SPOILER] - Prompt di supporto – Esercizio 11 _Meeting‑Minutes Synthesizer_.docx', spoiler: true }
      ]
    },
    {
      id: '05',
      title: 'Creazione Template',
      icon: FileCheck,
      color: 'from-orange-500 to-amber-500',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-300',
      description: 'Crea un template di valutazione del personale.',
      files: [
        { name: 'Istruzioni.docx', path: 'Esercizi/05_Creazione_template/Istruzioni.docx' },
        { name: 'Template di valutazione.docx', path: 'Esercizi/05_Creazione_template/Materiale/Template di valutazione.docx' },
        { name: 'Valutazione Alessia Conti.docx', path: 'Esercizi/05_Creazione_template/Materiale/Valutazione Alessia Conti.docx' },
        { name: 'Valutazione Davide Moretti.docx', path: 'Esercizi/05_Creazione_template/Materiale/Valutazione Davide Moretti.docx' },
        { name: 'Valutazione Marco Rossi.docx', path: 'Esercizi/05_Creazione_template/Materiale/Valutazione Marco Rossi.docx' },
        { name: 'Appunti 1_1 Alessia e Davide.docx', path: 'Esercizi/05_Creazione_template/Materiale/Appunti 1_1 Alessia e Davide.docx' },
        { name: 'Appunti 1_1 Marco.docx', path: 'Esercizi/05_Creazione_template/Materiale/Appunti 1_1 Marco.docx' },
        { name: '[SPOILER] Prompt di supporto.docx', path: 'Esercizi/05_Creazione_template/[SPOILER] - Prompt di supporto.docx', spoiler: true }
      ]
    },
    {
      id: '06',
      title: 'Template Descrizione Processi',
      icon: Workflow,
      color: 'from-teal-500 to-cyan-500',
      bgColor: 'bg-teal-50',
      borderColor: 'border-teal-300',
      description: 'Crea template per la descrizione di processi aziendali.',
      files: [
        { name: 'Istruzioni.docx', path: 'Esercizi/06_Template_per_descrizione_processo/Istruzioni.docx' },
        { name: 'Processi A_B_C.docx', path: 'Esercizi/06_Template_per_descrizione_processo/Processi A_B_C.docx' },
        { name: 'Processo D - Descrizione grezza.docx', path: 'Esercizi/06_Template_per_descrizione_processo/Processo D – Descrizione grezza (da strutturare).docx' },
        { name: '[SPOILER] Prompt di supporto.docx', path: 'Esercizi/06_Template_per_descrizione_processo/[Spoiler] - Prompt di supporto – Compliance_ descrizione processi.docx', spoiler: true }
      ]
    },
    {
      id: '06B',
      title: 'Ridisegnare i Processi',
      icon: Users,
      color: 'from-indigo-500 to-blue-500',
      bgColor: 'bg-indigo-50',
      borderColor: 'border-indigo-300',
      description: 'Ridisegna il processo di valutazione delle persone.',
      files: [
        { name: 'Istruzioni - Valutazione delle persone.docx', path: "Esercizi/06B_Ridisegnare i processi/Istruzioni dell'esercizio – Valutazione delle persone.docx" },
        { name: 'Scheda di valutazione.docx', path: 'Esercizi/06B_Ridisegnare i processi/Materiale/Scheda di valutazione.docx' },
        { name: 'Tre descrizioni da manager diversi.docx', path: 'Esercizi/06B_Ridisegnare i processi/Materiale/Tre descrizioni da manager diversi.docx' },
        { name: 'Appunti non strutturati del manager diretto.docx', path: 'Esercizi/06B_Ridisegnare i processi/Materiale/Appunti non strutturati del manager diretto.docx' },
        { name: '[SPOILER] Prompt di supporto.docx', path: 'Esercizi/06B_Ridisegnare i processi/[Spoiler] - PROMPT DI SUPPORTO.docx', spoiler: true }
      ]
    },
    {
      id: '07',
      title: 'Risoluzione Conflitti',
      icon: MessageSquare,
      color: 'from-red-500 to-pink-500',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-300',
      description: 'Gestisci e risolvi conflitti aziendali analizzando le comunicazioni.',
      files: [
        { name: 'Istruzioni - Gestione e risoluzione di un conflitto.docx', path: 'Esercizi/07_Risoluzione conflitti/Istruzioni - Gestione e risoluzione di un conflitto.docx' },
        { name: 'Appunti del manager.docx', path: 'Esercizi/07_Risoluzione conflitti/Materiali/Appunti del manager.docx' },
        { name: 'Chat interne.docx', path: 'Esercizi/07_Risoluzione conflitti/Materiali/Chat interne.docx' },
        { name: 'Email HR.docx', path: 'Esercizi/07_Risoluzione conflitti/Materiali/Email HR.docx' },
        { name: 'Email Manager.docx', path: 'Esercizi/07_Risoluzione conflitti/Materiali/Email Manager.docx' },
        { name: 'Email reparto scientifico.docx', path: 'Esercizi/07_Risoluzione conflitti/Materiali/Email reparto scientifico.docx' },
        { name: 'POLICY AZIENDALE (ESTRATTO).docx', path: 'Esercizi/07_Risoluzione conflitti/Materiali/DOCUMENTO_ POLICY AZIENDALE (ESTRATTO).docx' },
        { name: '[SPOILER] Prompt di supporto.docx', path: 'Esercizi/07_Risoluzione conflitti/[Spoiler] - PROMPT DI SUPPORTO.docx', spoiler: true }
      ]
    }
  ];

  const currentExercise = exercises[activeTab];
  const assetBase = import.meta.env.BASE_URL;
  const baseDirectory = currentExercise.files[0]?.path
    ? currentExercise.files[0].path.split('/').slice(0, -1).join('/')
    : '';
  const downloadHref = baseDirectory
    ? `${assetBase}${encodeURI(`${baseDirectory}.zip`)}`
    : null;
  const Icon = currentExercise.icon;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex flex-col items-center justify-center gap-3 mb-3">
            <img
              src={datapizzaLogo}
              alt="Logo Datapizza"
              className="w-16 h-16 md:w-20 md:h-20 object-contain drop-shadow-md"
            />
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              Esercizi Datapizza
            </h1>
          </div>
          <p className="text-slate-600 text-lg">
            Seleziona un esercizio e scarica i materiali necessari
          </p>
          <div className="mt-6 flex justify-center">
            <a
              href="doubt_GSK.html"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-purple-600 to-pink-600 shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-transform duration-200"
            >
              <Sparkles size={18} className="text-white" />
              <span>Approfondisci i tuoi dubbi su AI</span>
            </a>
          </div>
        </div>

        {/* Tabs Navigation */}
        <div className="bg-white rounded-2xl shadow-lg p-2 mb-6 overflow-x-auto">
          <div className="flex gap-2 min-w-max">
            {exercises.map((exercise, index) => {
              const TabIcon = exercise.icon;
              return (
                <button
                  key={exercise.id}
                  onClick={() => setActiveTab(index)}
                  className={`flex items-center gap-2 px-4 py-3 rounded-xl font-medium transition-all duration-300 whitespace-nowrap ${
                    activeTab === index
                      ? `bg-gradient-to-r ${exercise.color} text-white shadow-md scale-105`
                      : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <TabIcon size={18} />
                  <span className="text-sm">{exercise.title}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Exercise Content */}
        <div className={`${currentExercise.bgColor} rounded-2xl shadow-xl p-6 md:p-8 border-2 ${currentExercise.borderColor}`}>
          {/* Exercise Header */}
          <div className="flex items-start gap-4 mb-6">
            <div className={`p-4 rounded-xl bg-gradient-to-r ${currentExercise.color} shadow-lg`}>
              <Icon size={32} className="text-white" />
            </div>
            <div className="flex-1">
              <h2 className="text-3xl font-bold text-slate-800 mb-2">
                Esercizio {currentExercise.id}: {currentExercise.title}
              </h2>
              <p className="text-slate-600 text-lg">
                {currentExercise.description}
              </p>
            </div>
          </div>

          {/* Files Section */}
          <div className="bg-white rounded-xl p-6 shadow-md">
            <h3 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
              <Download size={24} className="text-slate-600" />
              File da scaricare
            </h3>
            
            <div className="grid gap-3">
              {currentExercise.files.map((file) => (
                <a
                  key={file.path}
                  href={`${assetBase}${encodeURI(file.path)}`}
                  className={`flex items-center justify-between p-4 rounded-lg border-2 transition-all duration-200 hover:scale-105 hover:shadow-md ${
                    file.spoiler
                      ? 'bg-yellow-50 border-yellow-300 hover:bg-yellow-100'
                      : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
                  }`}
                  download
                >
                  <div className="flex items-center gap-3">
                    <FileText size={20} className={file.spoiler ? 'text-yellow-600' : 'text-slate-600'} />
                    <span className={`font-medium ${file.spoiler ? 'text-yellow-900' : 'text-slate-700'}`}>
                      {file.name}
                    </span>
                    {file.spoiler && (
                      <span className="px-2 py-1 bg-yellow-400 text-yellow-900 text-xs font-bold rounded-full">
                        SPOILER
                      </span>
                    )}
                  </div>
                  <Download size={18} className={file.spoiler ? 'text-yellow-600' : 'text-slate-400'} />
                </a>
              ))}
            </div>

            {/* Download All Button */}
            <div className="mt-6 pt-6 border-t-2 border-slate-200">
              <a
                href={downloadHref ?? '#'}
                className={`block w-full text-center py-4 rounded-xl font-bold text-white bg-gradient-to-r ${currentExercise.color} hover:scale-105 transition-all duration-200 shadow-lg hover:shadow-xl`}
                download
                {...(downloadHref ? {} : { 'aria-disabled': true })}
              >
                📦 Scarica cartella completa esercizio {currentExercise.id}
              </a>
            </div>
          </div>

          <div className="mt-8">
            <ExerciseTimer
              defaultMinutes={30}
              accentGradient={currentExercise.color}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-slate-500 text-sm">
          <p>Esercizio {activeTab + 1} di {exercises.length}</p>
        </div>
      </div>
    </div>
  );
};

export default EserciziDataPizza;
