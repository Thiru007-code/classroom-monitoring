import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AnalysisProvider } from './context/AnalysisContext';
import { AnalysisBanner } from './components/AnalysisBanner';
import { DashboardPage } from './pages/DashboardPage';
import { AnalyzePage } from './pages/AnalyzePage';
import { HistoryPage } from './pages/HistoryPage';
import { InstitutionDetailsPage } from './pages/InstitutionDetailsPage';

export function App() {
  return (
    <AnalysisProvider>
      <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-600 selection:text-white">
          <Navbar />
          <AnalysisBanner />
          
          <main className="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <ErrorBoundary>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/analyze" element={<AnalyzePage />} />
                <Route path="/history" element={<HistoryPage />} />
                <Route path="/institutions" element={<InstitutionDetailsPage />} />
              </Routes>
            </ErrorBoundary>
          </main>

          <Footer />
        </div>
      </Router>
    </AnalysisProvider>
  );
}

export default App;
