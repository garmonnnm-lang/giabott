import { useEffect, useState } from 'react';
import { Bot, Terminal, Server, CheckCircle, XCircle, Users, BookOpen } from 'lucide-react';

export default function App() {
  const [stats, setStats] = useState<{ botRunning: boolean; registeredUsers: number; totalQuestions: number } | null>(null);

  useEffect(() => {
    const fetchStats = () => {
      fetch('/api/stats')
        .then(res => res.json())
        .then(data => setStats(data))
        .catch(console.error);
    };
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-neutral-900 text-neutral-100 p-6 md:p-12 font-sans selection:bg-blue-500/30">
      <div className="max-w-4xl mx-auto space-y-12">
        <header className="space-y-4">
          <div className="inline-flex items-center gap-3 bg-neutral-800 border border-neutral-700 px-4 py-2 rounded-full text-sm">
            <Bot className="w-5 h-5 text-blue-400" />
            <span className="font-medium">Telegram ГИА Бот</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-white">
            Система управления <br/> Telegram-ботом
          </h1>
          <p className="text-neutral-400 max-w-2xl text-lg">
            Ваш бот для подготовки к ГИА работает здесь. В этой панели отображаются системные показатели и инструкции по развёртыванию на <span className="text-white">Render.com</span>.
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-neutral-800 border border-neutral-700 rounded-2xl p-6 flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <Server className="text-purple-400 w-6 h-6" />
              <h3 className="font-semibold text-lg">Статус Бота</h3>
            </div>
            <div className="flex items-center gap-3 text-2xl font-medium">
              {stats === null ? (
                <span className="text-neutral-500 animate-pulse">Загрузка...</span>
              ) : stats.botRunning ? (
                <>
                  <CheckCircle className="text-green-400 w-8 h-8" />
                  <span className="text-green-50">Онлайн</span>
                </>
              ) : (
                <>
                  <XCircle className="text-red-400 w-8 h-8" />
                  <span className="text-red-50">Офлайн</span>
                </>
              )}
            </div>
            {!stats?.botRunning && (
              <p className="text-sm text-red-300">
                Добавьте TELEGRAM_BOT_TOKEN в переменные окружения.
              </p>
            )}
          </div>

          <div className="bg-neutral-800 border border-neutral-700 rounded-2xl p-6 flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <Users className="text-emerald-400 w-6 h-6" />
              <h3 className="font-semibold text-lg">Язык бота</h3>
            </div>
            <div className="text-4xl font-semibold text-emerald-50">
              Python
            </div>
            <p className="text-sm text-neutral-400">Переписан на pyTelegramBotAPI.</p>
          </div>

          <div className="bg-neutral-800 border border-neutral-700 rounded-2xl p-6 flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <BookOpen className="text-orange-400 w-6 h-6" />
              <h3 className="font-semibold text-lg">База задач</h3>
            </div>
            <div className="text-4xl font-semibold text-orange-50">
              30
            </div>
            <p className="text-sm text-neutral-400">Медицинских задач в пуле.</p>
          </div>
        </div>

        <section className="bg-neutral-800 border border-neutral-700 rounded-3xl p-8 space-y-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
            <Terminal className="w-32 h-32" />
          </div>
          
          <h2 className="text-2xl font-semibold">🚀 Инструкция для Render.com</h2>
          <p className="text-neutral-300 leading-relaxed max-w-3xl">
            Код вашего бота полностью готов к развёртыванию на Render. В корне проекта уже создан файл <code>render.yaml</code> (Blueprints), который автоматически настроит сервер.
          </p>

          <ol className="list-decimal list-inside space-y-4 text-neutral-300 max-w-3xl">
            <li>Запушьте данный проект в свой GitHub-репозиторий.</li>
            <li>Зайдите на <a href="https://dashboard.render.com/blueprints" target="_blank" rel="noreferrer" className="text-blue-400 underline">Render Blueprints</a> и подключите свой репозиторий.</li>
            <li>Render автоматически прочитает <code>render.yaml</code> и создаст Web Service.</li>
            <li>В панели настроек сервиса на Render <strong className="text-white">обязательно</strong> добавьте переменную окружения:<br />
              <code className="bg-neutral-900 px-3 py-1.5 rounded-lg text-blue-300 mt-2 inline-block">TELEGRAM_BOT_TOKEN="ВАШ_ТОКЕН"</code>
            </li>
            <li>Запустите проект — ваш бот (Python) и дашборд (React) будут работать!</li>
          </ol>
        </section>
      </div>
    </div>
  );
}
