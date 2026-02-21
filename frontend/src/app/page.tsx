"use client";

import { useState } from "react";
import axios from "axios";
import { UploadCloud, CheckCircle, Loader2, AlertCircle, FileText, Database, Sparkles, MoveRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [extractedData, setExtractedData] = useState<any>(null);
  const [recordId, setRecordId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isConfirming, setIsConfirming] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setPreviewUrl(URL.createObjectURL(selectedFile));
      setError(null);
    }
  };

  const clearFile = (e: React.MouseEvent) => {
    e.preventDefault();
    setFile(null);
    setPreviewUrl(null);
  }

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(`${API_URL}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (response.data.status === "error") {
        setError(response.data.message);
      } else {
        setRecordId(response.data.record_id);
        setExtractedData(response.data.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "An error occurred during extraction.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleConfirm = async () => {
    if (!recordId || !extractedData) return;
    setIsConfirming(true);
    setError(null);

    try {
      await axios.post(`${API_URL}/confirm/${recordId}`, extractedData);
      setSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || "An error occurred while confirming data.");
    } finally {
      setIsConfirming(false);
    }
  };

  const handleEditChange = (index: number, field: string, value: string) => {
    const newData = { ...extractedData };
    newData.entries[index][field] = value;
    setExtractedData(newData);
  };

  return (
    <main className="min-h-screen bg-[#0A0A0B] text-slate-300 font-sans selection:bg-indigo-500/30 overflow-hidden relative">

      {/* Background Glow Effects */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] opacity-20 bg-indigo-500 blur-[150px] rounded-full pointer-events-none" />
      <div className="absolute bottom-0 right-[-20%] w-[600px] h-[600px] opacity-10 bg-blue-500 blur-[150px] rounded-full pointer-events-none" />

      {/* Navbar Branding */}
      <nav className="relative z-10 border-b border-white/5 bg-white/[0.02] backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center shadow-[0_0_20px_rgba(99,102,241,0.4)]">
              <Database className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white tracking-tight">AirStore</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-medium text-indigo-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
              System Active
            </span>
          </div>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-16 md:py-24 relative z-10">

        {/* Header */}
        <header className="mb-16 text-center max-w-2xl mx-auto">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight mb-6 text-white"
          >
            Digitize ledgers with <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-blue-400">AI precision.</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-lg text-slate-400 font-light"
          >
            Upload handwritten records in English, Hindi, or Marathi. AirStore intelligently extracts, translates, and syncs your data directly to Google Sheets.
          </motion.p>
        </header>

        <AnimatePresence mode="wait">
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-8 p-4 bg-red-500/10 text-red-400 rounded-2xl flex items-start gap-3 border border-red-500/20 max-w-3xl mx-auto shadow-2xl backdrop-blur-md"
            >
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <p className="text-sm font-medium">{error}</p>
            </motion.div>
          )}

          {success ? (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white/5 backdrop-blur-xl rounded-[2rem] border border-white/10 p-12 text-center max-w-2xl mx-auto shadow-2xl relative overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-green-500/10 to-transparent opacity-50 pointer-events-none" />

              <div className="inline-flex items-center justify-center w-20 h-20 bg-green-500/20 text-green-400 rounded-full mb-8 shadow-[0_0_40px_rgba(34,197,94,0.3)]">
                <CheckCircle className="w-10 h-10" />
              </div>
              <h2 className="text-3xl font-bold text-white mb-4">Sync Successful</h2>
              <p className="text-slate-400 mb-10 text-lg">Your entries have been securely digitized and appended to your connected AirStore Sheet.</p>

              <button
                onClick={() => window.location.reload()}
                className="px-8 py-4 bg-white text-black font-semibold rounded-2xl hover:bg-slate-200 transition shadow-[0_0_30px_rgba(255,255,255,0.2)] flex items-center gap-2 mx-auto"
              >
                Upload Next Record <MoveRight className="w-5 h-5" />
              </button>
            </motion.div>

          ) : extractedData ? (

            /* Confirmation State */
            <motion.div
              key="confirmation"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-[#111113] rounded-[2rem] border border-white/10 shadow-2xl overflow-hidden max-w-4xl mx-auto relative spotlight"
            >
              <div className="p-8 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
                <div>
                  <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                    <Sparkles className="w-6 h-6 text-indigo-400" />
                    Review Extraction
                  </h2>
                  <p className="text-sm text-slate-400 mt-2">Make any necessary corrections before AirStore pushes this to your database.</p>
                </div>
              </div>

              <div className="p-2 sm:p-6 overflow-x-auto">
                <table className="w-full text-left border-collapse min-w-[600px]">
                  <thead>
                    <tr className="border-b border-white/10 text-xs uppercase tracking-wider font-semibold text-slate-500">
                      <th className="pb-4 pl-4 min-w-[120px]">Date</th>
                      <th className="pb-4 sm:px-4 w-full">Description / Name</th>
                      <th className="pb-4 sm:px-4 text-right min-w-[120px]">Amount</th>
                      <th className="pb-4 pr-4 sm:px-4 min-w-[140px]">Status</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm">
                    {extractedData.entries.map((req: any, i: number) => (
                      <tr key={i} className="border-b border-white/5 last:border-0 hover:bg-white/[0.02] transition-colors group">
                        <td className="py-3 pl-4">
                          <input
                            className="bg-transparent text-slate-300 w-full px-3 py-2 focus:bg-[#1A1A1D] focus:ring-1 focus:ring-indigo-500/50 rounded-lg outline-none transition border border-transparent group-hover:border-white/10"
                            value={req.date}
                            onChange={(e) => handleEditChange(i, 'date', e.target.value)}
                          />
                        </td>
                        <td className="py-3 sm:px-2">
                          <input
                            className="bg-transparent text-white font-medium w-full px-3 py-2 focus:bg-[#1A1A1D] focus:ring-1 focus:ring-indigo-500/50 rounded-lg outline-none transition border border-transparent group-hover:border-white/10"
                            value={req.name}
                            onChange={(e) => handleEditChange(i, 'name', e.target.value)}
                          />
                        </td>
                        <td className="py-3 sm:px-2">
                          <input
                            type="number"
                            className="bg-transparent text-indigo-300 font-semibold w-full px-3 py-2 text-right focus:bg-[#1A1A1D] focus:ring-1 focus:ring-indigo-500/50 rounded-lg outline-none transition border border-transparent group-hover:border-white/10"
                            value={req.amount}
                            onChange={(e) => handleEditChange(i, 'amount', e.target.value)}
                          />
                        </td>
                        <td className="py-3 pr-4 sm:px-2">
                          <input
                            className="bg-transparent text-slate-400 w-full px-3 py-2 focus:bg-[#1A1A1D] focus:ring-1 focus:ring-indigo-500/50 rounded-lg outline-none transition border border-transparent group-hover:border-white/10"
                            value={req.status}
                            onChange={(e) => handleEditChange(i, 'status', e.target.value)}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="p-6 border-t border-white/5 bg-[#0A0A0B]/50 flex justify-end gap-4 items-center">
                <button
                  onClick={() => setExtractedData(null)}
                  className="px-6 py-3 text-sm font-medium text-slate-400 hover:text-white transition"
                  disabled={isConfirming}
                >
                  Discard
                </button>
                <button
                  onClick={handleConfirm}
                  disabled={isConfirming}
                  className="px-8 py-3 text-sm font-semibold bg-gradient-to-r from-indigo-500 to-blue-600 text-white rounded-xl shadow-[0_0_20px_rgba(99,102,241,0.3)] hover:shadow-[0_0_30px_rgba(99,102,241,0.5)] transition hover:scale-[1.02] active:scale-95 disabled:opacity-70 disabled:hover:scale-100 flex items-center gap-2"
                >
                  {isConfirming ? <Loader2 className="w-5 h-5 animate-spin" /> : <Database className="w-5 h-5" />}
                  {isConfirming ? 'Pushing to AirStore...' : 'Confirm & Sync'}
                </button>
              </div>
            </motion.div>

          ) : (

            /* Upload State */
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="max-w-3xl mx-auto"
            >
              <div className="bg-[#111113]/80 backdrop-blur-xl rounded-[2rem] p-8 md:p-12 border border-white/10 shadow-2xl relative group pb-10">

                <div className="absolute inset-0 bg-gradient-to-b from-white/[0.03] to-transparent pointer-events-none rounded-[2rem]" />

                {!previewUrl ? (
                  <label className="relative flex flex-col items-center justify-center w-full h-[320px] border border-dashed border-white/20 rounded-3xl cursor-pointer bg-white/[0.01] hover:bg-white/[0.03] hover:border-indigo-500/50 transition-all duration-300">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      <div className="w-20 h-20 bg-[#1A1A1D] rounded-full flex items-center justify-center mb-6 shadow-inner border border-white/5 group-hover:scale-110 transition duration-500 group-hover:shadow-[0_0_30px_rgba(99,102,241,0.2)]">
                        <FileText className="w-8 h-8 text-slate-400 group-hover:text-indigo-400 transition" />
                      </div>
                      <p className="mb-3 text-lg text-slate-300 font-medium tracking-wide">
                        <span className="text-indigo-400 font-semibold">Upload a ledger</span> or drag & drop
                      </p>
                      <p className="text-sm text-slate-500">Supports JPG, PNG (Max 10MB)</p>
                    </div>
                    <input type="file" className="hidden" accept="image/*" onChange={handleFileChange} />
                  </label>
                ) : (
                  <div className="relative w-full h-[320px] rounded-3xl overflow-hidden border border-white/10 group/img shadow-2xl">
                    <img src={previewUrl} className="w-full h-full object-cover transition duration-500 group-hover/img:scale-105 group-hover/img:opacity-50" alt="Preview" />
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover/img:opacity-100 transition-opacity duration-300 bg-black/40 backdrop-blur-sm gap-4">
                      <label className="px-6 py-3 bg-white/10 hover:bg-white/20 text-white rounded-xl font-medium backdrop-blur-md cursor-pointer transition border border-white/10">
                        Change Image
                        <input type="file" className="hidden" accept="image/*" onChange={handleFileChange} />
                      </label>
                      <button onClick={clearFile} className="px-6 py-3 bg-red-500/20 hover:bg-red-500/30 text-red-200 rounded-xl font-medium backdrop-blur-md transition border border-red-500/20">
                        Clear
                      </button>
                    </div>
                  </div>
                )}

                <div className="mt-10 flex justify-center">
                  <button
                    onClick={handleUpload}
                    disabled={!file || isUploading}
                    className={`
                      w-full relative overflow-hidden md:w-auto min-w-[280px] px-8 py-4 rounded-2xl font-bold tracking-wide transition-all duration-300 flex items-center justify-center gap-3
                      ${!file
                        ? 'bg-[#1A1A1D] text-slate-500 cursor-not-allowed border border-white/5'
                        : 'bg-white text-black hover:bg-slate-200 hover:scale-[1.02] shadow-[0_0_40px_rgba(255,255,255,0.15)]'}
                    `}
                  >
                    {isUploading && (
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/50 to-transparent w-[200%] animate-[shimmer_2s_infinite]" />
                    )}

                    {isUploading ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin relative z-10" />
                        <span className="relative z-10">Running AirStore Analysis...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className={`w-5 h-5 ${file ? 'text-indigo-600' : ''}`} />
                        <span>Run Intelligence Engine</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </main>
  );
}
