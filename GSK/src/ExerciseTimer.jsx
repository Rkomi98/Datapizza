import React, { useEffect, useMemo, useState } from 'react';
import { Clock, Pause, Play, RotateCcw } from 'lucide-react';

const QUICK_PRESETS = [10, 15, 20, 25, 30, 45];

const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
};

const ExerciseTimer = ({
  defaultMinutes = 30,
  accentGradient = 'from-purple-500 to-pink-500',
}) => {
  const [minutesInput, setMinutesInput] = useState(String(defaultMinutes));
  const [totalSeconds, setTotalSeconds] = useState(defaultMinutes * 60);
  const [remainingSeconds, setRemainingSeconds] = useState(defaultMinutes * 60);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    const baseSeconds = defaultMinutes * 60;
    setMinutesInput(String(defaultMinutes));
    setTotalSeconds(baseSeconds);
    setRemainingSeconds(baseSeconds);
    setIsRunning(false);
  }, [defaultMinutes]);

  useEffect(() => {
    if (!isRunning) {
      return undefined;
    }

    const tick = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          setIsRunning(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(tick);
  }, [isRunning]);

  const progress = useMemo(() => {
    if (totalSeconds === 0) {
      return 0;
    }
    const elapsed = totalSeconds - remainingSeconds;
    const raw = (elapsed / totalSeconds) * 100;
    return Math.min(100, Math.max(0, raw));
  }, [remainingSeconds, totalSeconds]);

  const applyDuration = (minutes) => {
    const safeMinutes = Math.max(1, Math.round(minutes));
    const seconds = safeMinutes * 60;
    setMinutesInput(String(safeMinutes));
    setTotalSeconds(seconds);
    setRemainingSeconds(seconds);
    setIsRunning(false);
  };

  const handleDurationSubmit = (event) => {
    event.preventDefault();
    const parsed = Number(minutesInput);
    if (Number.isNaN(parsed) || parsed <= 0) {
      setMinutesInput(String(Math.max(1, Math.round(totalSeconds / 60))));
      return;
    }
    applyDuration(parsed);
  };

  const handlePresetClick = (minutes) => {
    applyDuration(minutes);
  };

  const toggleRunning = () => {
    if (remainingSeconds === 0) {
      setRemainingSeconds(totalSeconds);
    }
    setIsRunning((prev) => !prev && totalSeconds > 0);
  };

  const handleReset = () => {
    setRemainingSeconds(totalSeconds);
    setIsRunning(false);
  };

  return (
    <div className="relative overflow-hidden rounded-2xl border-2 border-slate-200 bg-white shadow-lg">
      <div className="absolute inset-x-0 top-0 h-1 bg-slate-200">
        <div
          className={`h-full rounded-tr-full rounded-br-full bg-gradient-to-r ${accentGradient}`}
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="relative z-10 grid gap-6 p-6 md:p-8">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-4">
            <div
              className={`flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-r ${accentGradient} text-white shadow-md`}
            >
              <Clock size={28} />
            </div>
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">
                Timer focus
              </p>
              <h3 className="text-2xl font-bold text-slate-900">
                Countdown personalizzabile
              </h3>
            </div>
          </div>
          <form
            className="flex items-center gap-3"
            onSubmit={handleDurationSubmit}
          >
            <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 shadow-inner">
              <span className="text-sm font-medium text-slate-500">
                Minuti
              </span>
              <input
                type="number"
                min="1"
                value={minutesInput}
                onChange={(event) => setMinutesInput(event.target.value)}
                className="w-16 rounded-lg border border-slate-200 bg-white px-3 py-1 text-center text-base font-semibold text-slate-700 focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-200"
              />
            </div>
            <button
              type="submit"
              className={`inline-flex items-center gap-2 rounded-xl bg-gradient-to-r ${accentGradient} px-4 py-2 text-sm font-semibold text-white shadow-md transition-transform duration-200 hover:-translate-y-0.5 hover:shadow-lg`}
            >
              Imposta
            </button>
          </form>
        </div>

        <div className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
          <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 p-6 text-center shadow-inner">
            <div
              className="absolute inset-0 opacity-40"
              style={{
                backgroundImage: 'radial-gradient(circle at top, rgba(99,102,241,0.25), transparent 60%)',
              }}
            />
            <div className="relative z-10 flex flex-col items-center gap-2">
              <span className="text-sm font-medium uppercase tracking-[0.3em] text-slate-500">
                Tempo residuo
              </span>
              <span className="font-mono text-5xl font-bold tabular-nums text-slate-900 md:text-6xl">
                {formatTime(remainingSeconds)}
              </span>
              <p className="text-sm text-slate-500">
                {Math.ceil(remainingSeconds / 60)} minuti stimati
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-3">
            <button
              type="button"
              onClick={toggleRunning}
              className={`inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 shadow-md transition-all duration-200 hover:-translate-y-0.5 hover:bg-slate-50 hover:shadow-lg ${
                isRunning ? 'ring-2 ring-offset-2 ring-slate-200' : ''
              }`}
            >
              {isRunning ? <Pause size={18} /> : <Play size={18} />}
              {isRunning ? 'Pausa' : 'Avvia'}
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-5 py-3 text-sm font-semibold text-slate-600 transition-all duration-200 hover:-translate-y-0.5 hover:bg-white hover:shadow-lg"
            >
              <RotateCcw size={18} />
              Reset
            </button>
          </div>
        </div>

        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
            Seleziona un preset
          </p>
          <div className="flex flex-wrap gap-2">
            {QUICK_PRESETS.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => handlePresetClick(option)}
                className={`rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition-all duration-200 hover:-translate-y-0.5 hover:border-slate-300 hover:bg-white ${
                  Number(minutesInput) === option && !isRunning
                    ? `bg-gradient-to-r ${accentGradient} text-white shadow-md`
                    : 'bg-slate-50'
                }`}
              >
                {option} min
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExerciseTimer;
