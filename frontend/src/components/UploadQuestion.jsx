import { useEffect, useRef, useState } from "react";
import { GlobalWorkerOptions, getDocument } from "pdfjs-dist";
import pdfWorkerUrl from "pdfjs-dist/build/pdf.worker.mjs?url";
import { analyzeCircuit } from "../services/api";

GlobalWorkerOptions.workerSrc = pdfWorkerUrl;

function UploadQuestion({ onAnalysisComplete, apiKey, onOpenSettings }) {
  const [file, setFile] = useState(null);
  const [imageUrl, setImageUrl] = useState("");
  const [pdfDocument, setPdfDocument] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [question, setQuestion] = useState("");
  const [cropRect, setCropRect] = useState(null);
  const [cropDraft, setCropDraft] = useState(null);
  const [cropStart, setCropStart] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [rendering, setRendering] = useState(false);
  const canvasRef = useRef(null);
  const cropFrameRef = useRef(null);
  const previewUrlRef = useRef("");
  const fileInputRef = useRef(null);
  const pdfLoadingTaskRef = useRef(null);

  useEffect(() => {
    if (!pdfDocument || !canvasRef.current) return undefined;
    let cancelled = false;
    const renderPage = async () => {
      setRendering(true);
      try {
        const page = await pdfDocument.getPage(pageNumber);
        const viewport = page.getViewport({ scale: 1.7 });
        const canvas = canvasRef.current;
        const context = canvas.getContext("2d", { alpha: false });
        canvas.width = Math.ceil(viewport.width);
        canvas.height = Math.ceil(viewport.height);
        await page.render({ canvasContext: context, viewport }).promise;
        if (!cancelled) setImageUrl(canvas.toDataURL("image/png"));
      } catch (renderError) {
        if (!cancelled) setError(`Could not render this PDF page: ${renderError.message}`);
      } finally {
        if (!cancelled) setRendering(false);
      }
    };
    renderPage();
    return () => { cancelled = true; };
  }, [pdfDocument, pageNumber]);

  useEffect(() => () => {
    if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
  }, []);

  // PDFDocumentProxy does not expose destroy() in all pdfjs-dist versions;
  // the loading task owns that lifecycle method instead.
  useEffect(() => () => {
    const task = pdfLoadingTaskRef.current;
    pdfLoadingTaskRef.current = null;
    if (typeof task?.destroy === "function") void task.destroy().catch(() => {});
  }, []);

  const chooseFile = async (event) => {
    const selected = event.target.files?.[0];
    if (!selected) return;
    setError("");
    setFile(selected);
    setImageUrl("");
    setPdfDocument(null);
    setPageNumber(1);
    setQuestion("");
    if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    if (typeof pdfLoadingTaskRef.current?.destroy === "function") {
      void pdfLoadingTaskRef.current.destroy().catch(() => {});
      pdfLoadingTaskRef.current = null;
    }

    if (selected.type === "application/pdf" || selected.name.toLowerCase().endsWith(".pdf")) {
      try {
        const loadingTask = getDocument({ data: await selected.arrayBuffer() });
        pdfLoadingTaskRef.current = loadingTask;
        const pdf = await loadingTask.promise;
        if (pdfLoadingTaskRef.current !== loadingTask) return;
        setPdfDocument(pdf);
      } catch (loadError) {
        if (loadError?.name === "AbortException") return;
        setError(`Could not open this PDF: ${loadError.message}`);
      }
      return;
    }

    const url = URL.createObjectURL(selected);
    previewUrlRef.current = url;
    setImageUrl(url);
  };

  const handleAnalyze = async () => {
    if (!file || !imageUrl || rendering) return;
    try {
      setLoading(true);
      setError("");
      let pageImage = file;
      let sourcePage = file;
      if (pdfDocument) {
        const sourceCanvas = canvasRef.current;
        const makePng = (canvas) => new Promise((resolve, reject) => {
          canvas.toBlob((value) => value ? resolve(value) : reject(new Error("Could not prepare this page for analysis.")), "image/png");
        });
        const pageBlob = await makePng(sourceCanvas);
        sourcePage = new File([pageBlob], `${file.name.replace(/\.pdf$/i, "")}-page-${pageNumber}.png`, { type: "image/png" });
        if (cropRect) {
          const left = Math.round(cropRect.x * sourceCanvas.width);
          const top = Math.round(cropRect.y * sourceCanvas.height);
          const width = Math.max(1, Math.round(cropRect.width * sourceCanvas.width));
          const height = Math.max(1, Math.round(cropRect.height * sourceCanvas.height));
          const croppedCanvas = document.createElement("canvas");
          croppedCanvas.width = width;
          croppedCanvas.height = height;
          croppedCanvas.getContext("2d", { alpha: false }).drawImage(sourceCanvas, left, top, width, height, 0, 0, width, height);
          const cropBlob = await makePng(croppedCanvas);
          pageImage = new File([cropBlob], `${file.name.replace(/\.pdf$/i, "")}-page-${pageNumber}-crop.png`, { type: "image/png" });
        } else {
          pageImage = sourcePage;
        }
      }
      const result = await analyzeCircuit(pageImage, apiKey, question.trim());
      const components = result?.vision?.circuit?.components;
      if (!Array.isArray(components) || components.length === 0) {
        throw new Error("PECTEN received a response but found no circuit components. Select a clearer crop that includes the whole circuit and its labels, or choose another image.");
      }
      onAnalysisComplete?.(result, pageImage, sourcePage, {
        fileName: file.name,
        pageNumber: pdfDocument ? pageNumber : null,
        question: question.trim(),
        cropRect,
      });
    } catch (analysisError) {
      setError(analysisError.message || "Could not analyze this page.");
    } finally {
      setLoading(false);
    }
  };

  const updateCrop = (event) => {
    const bounds = cropFrameRef.current?.getBoundingClientRect();
    if (!bounds || !cropStart) return;
    const x = Math.min(1, Math.max(0, (event.clientX - bounds.left) / bounds.width));
    const y = Math.min(1, Math.max(0, (event.clientY - bounds.top) / bounds.height));
    setCropDraft({ x: Math.min(cropStart.x, x), y: Math.min(cropStart.y, y),
      width: Math.abs(x - cropStart.x), height: Math.abs(y - cropStart.y) });
  };

  const beginCrop = (event) => {
    if (!pdfDocument) return;
    const bounds = cropFrameRef.current?.getBoundingClientRect();
    if (!bounds) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    const start = { x: Math.min(1, Math.max(0, (event.clientX - bounds.left) / bounds.width)),
      y: Math.min(1, Math.max(0, (event.clientY - bounds.top) / bounds.height)) };
    setCropStart(start);
    setCropDraft({ ...start, width: 0, height: 0 });
  };

  const finishCrop = () => {
    if (cropDraft && cropDraft.width > 0.015 && cropDraft.height > 0.015) setCropRect(cropDraft);
    else setCropRect(null);
    setCropDraft(null);
    setCropStart(null);
  };

  const changePage = (nextPage) => {
    setPageNumber(Math.min(pdfDocument.numPages, Math.max(1, nextPage)));
    setCropRect(null);
    setCropDraft(null);
    setCropStart(null);
  };

  const chooseAnotherFile = () => {
    if (typeof pdfLoadingTaskRef.current?.destroy === "function") {
      void pdfLoadingTaskRef.current.destroy().catch(() => {});
      pdfLoadingTaskRef.current = null;
    }
    if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    previewUrlRef.current = "";
    setFile(null);
    setImageUrl("");
    setPdfDocument(null);
    setCropRect(null);
    setCropDraft(null);
    setCropStart(null);
    setError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const quotaError = /quota|rate.?limit|429|resource_exhausted/i.test(error);
  const keyError = /api key|permission|unauthorized|forbidden/i.test(error);

  return (
    <section className="document-uploader" aria-labelledby="upload-heading">
      <div className="upload-intro">
        <p className="section-kicker">START WITH YOUR MATERIAL</p>
        <h1 id="upload-heading">Bring a physics question to life.</h1>
        <p>Upload a textbook page or circuit image. Choose the page and tell PECTEN what you want to find.</p>
      </div>

      <label className={`drop-zone${file ? " has-file" : ""}`} htmlFor="document-file">
        <span className="upload-symbol" aria-hidden="true">↑</span>
        <strong>{file ? file.name : "Choose a PDF or image"}</strong>
        <span>{file ? "Choose a different file" : "PDF, PNG, JPG, or WEBP"}</span>
        <input ref={fileInputRef} id="document-file" type="file" accept="application/pdf,image/png,image/jpeg,image/webp" onChange={chooseFile} />
      </label>

      {pdfDocument && <div className="page-picker">
        <label htmlFor="pdf-page">Page</label>
        <button type="button" aria-label="Previous page" disabled={pageNumber <= 1} onClick={() => changePage(pageNumber - 1)}>‹</button>
        <input id="pdf-page" type="number" min="1" max={pdfDocument.numPages} value={pageNumber}
          onChange={(event) => changePage(Number(event.target.value) || 1)} />
        <span>of {pdfDocument.numPages}</span>
        <button type="button" aria-label="Next page" disabled={pageNumber >= pdfDocument.numPages} onClick={() => changePage(pageNumber + 1)}>›</button>
      </div>}

      {file && <label className="question-field" htmlFor="student-question">
        <span>Your question <small>Optional</small></span>
        <textarea id="student-question" value={question} onChange={(event) => setQuestion(event.target.value)}
          placeholder="For example: Find the current through the 6 Ω resistor." rows="3" />
        <small>Paste the question from your page, or leave it blank and PECTEN will read what it can.</small>
      </label>}

      {error && <div className="upload-error-panel" role="alert">
        <strong>{quotaError ? "Gemini API limit reached" : keyError ? "Gemini key needs attention" : "PECTEN could not read this page"}</strong>
        <p>{error}</p>
        <div className="upload-error-actions">
          {(quotaError || keyError) && <button type="button" onClick={onOpenSettings}>Open Settings</button>}
          <button type="button" onClick={chooseAnotherFile}>Choose another image or PDF</button>
        </div>
      </div>}
      {file && <button type="button" className="analyze-button" onClick={handleAnalyze} disabled={loading || rendering || !imageUrl}>
        {loading ? "Reading the page…" : rendering ? "Preparing page…" : "Read question and build simulation"}
      </button>}

      {file && <div className="upload-preview">
        <div className="preview-heading"><strong>Page preview</strong>{pdfDocument && <span>Page {pageNumber}</span>}</div>
        {pdfDocument && <>
          <p className="crop-instructions">Drag over the question and circuit you want to simulate. If you skip this, PECTEN will read the whole page.</p>
          <div className="pdf-crop-frame" ref={cropFrameRef}>
            <canvas ref={canvasRef} aria-label={`PDF page ${pageNumber}`} />
            <div className="crop-selection-layer" onPointerDown={beginCrop} onPointerMove={updateCrop}
              onPointerUp={finishCrop} onPointerCancel={finishCrop} role="img" aria-label="Drag to select the question and circuit area">
              {(cropDraft || cropRect) && <div className="crop-selection-box" style={{
                left: `${(cropDraft || cropRect).x * 100}%`, top: `${(cropDraft || cropRect).y * 100}%`,
                width: `${(cropDraft || cropRect).width * 100}%`, height: `${(cropDraft || cropRect).height * 100}%`,
              }} />}
            </div>
          </div>
          {cropRect && <div className="crop-status"><span>Question area selected</span><button type="button" onClick={() => setCropRect(null)}>Clear selection</button></div>}
        </>}
        {imageUrl && !pdfDocument && <img src={imageUrl} alt="Selected question page" />}
      </div>}
    </section>
  );
}

export default UploadQuestion;
