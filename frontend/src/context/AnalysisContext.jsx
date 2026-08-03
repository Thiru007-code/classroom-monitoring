import React, { createContext, useContext, useState } from 'react';
import { api } from '../api/client';

const AnalysisContext = createContext(null);

export const AnalysisProvider = ({ children }) => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [activeInstitution, setActiveInstitution] = useState('');

  const runAnalysis = async (payload, selectedFile, previewUrl, institutionName) => {
    try {
      setIsAnalyzing(true);
      setError(null);
      setResult(null);
      setFile(selectedFile);
      setPreview(previewUrl);
      setActiveInstitution(institutionName || 'Classroom Inspection');

      const data = await api.analyzeClassroom(payload);
      setResult(data);
      setIsAnalyzing(false);
      return data;
    } catch (err) {
      console.error('Analysis background error:', err);
      const msg = err.response?.data?.detail || err.message || 'Failed to analyze classroom image.';
      setError(msg);
      setIsAnalyzing(false);
      throw err;
    }
  };

  const clearAnalysis = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    setIsAnalyzing(false);
  };

  return (
    <AnalysisContext.Provider
      value={{
        file,
        setFile,
        preview,
        setPreview,
        isAnalyzing,
        error,
        setError,
        result,
        setResult,
        activeInstitution,
        runAnalysis,
        clearAnalysis,
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
};

export const useAnalysis = () => {
  const context = useContext(AnalysisContext);
  if (!context) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return context;
};
