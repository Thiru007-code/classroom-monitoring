import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Uncaught UI Error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="glass-card rounded-2xl p-8 border border-rose-500/30 bg-rose-950/20 my-6 text-center">
          <div className="w-12 h-12 rounded-full bg-rose-500/20 flex items-center justify-center mx-auto mb-4 text-rose-400">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-white mb-1">Display Error</h3>
          <p className="text-xs text-rose-300 font-mono mb-4 max-w-md mx-auto">
            {this.state.error?.message || "An unexpected error occurred while rendering the results."}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-bold inline-flex items-center gap-2 border border-slate-700 transition-all"
          >
            <RefreshCw className="w-4 h-4" /> Reset Display
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
